"""User-installed live crease callback; no launcher, stage replacement or autoplay."""
import json,math
from pathlib import Path
from parcel_forge.crease_model import CreaseState,advance
from parcel_forge.evidence import make_unique_run_dir

class LiveCarton:
    def __init__(self,config):
        import omni.usd
        from pxr import UsdPhysics
        from isaacsim.core.simulation_manager import SimulationManager,SimulationEvent
        self.stage=omni.usd.get_context().get_stage();self.config=dict(config)
        self.joints={}
        for name in ['MajorYN','MajorYP','MinorXP','MinorXN']:
            joint=self.stage.GetPrimAtPath('/World/Carton/Hinge'+name);body=self.stage.GetPrimAtPath('/World/Carton/'+name)
            if not joint or not joint.IsA(UsdPhysics.RevoluteJoint) or not body.HasAPI(UsdPhysics.RigidBodyAPI) or UsdPhysics.RigidBodyAPI(body).GetRigidBodyEnabledAttr().Get()==False:
                raise ValueError('Load live asset.usda, not recording.usda; missing active flap '+name)
            self.joints['Hinge'+name]=UsdPhysics.DriveAPI(joint,'angular')
        self.bends=config.get('panel_bend_joints',{}) if config.get('panel_model')=='segmented_directional_strip_v1' else {}
        self.bend_initial={n:math.radians(UsdPhysics.DriveAPI(self.stage.GetPrimAtPath('/World/Carton/'+n),'angular').GetTargetPositionAttr().Get() or 0) for n in self.bends}
        self.initial={n:math.radians(d.GetTargetPositionAttr().Get() or 0) for n,d in self.joints.items()}
        self.out=Path(make_unique_run_dir('ext1_live_interaction'));self.view=None;self.states={};self.pulses={};self.elapsed=0.;self.samples=0;self.failed=False;self.last_targets=None;self.window=None;self.bend_states={};self.force_probe=None;self.closed=False
        self.manager=SimulationManager
        self.ids=[SimulationManager.register_callback(self._step,SimulationEvent.PHYSICS_PRE_STEP),SimulationManager.register_callback(self._reset,SimulationEvent.SIMULATION_STOPPED)]
        (self.out/'config.json').write_text(json.dumps(self.config,indent=2)+'\n')
        self._log({'event':'installed','human_mouse_interaction':'not_tested','source_stage':self.stage.GetRootLayer().identifier})
        gains=self.config.get('crease_gains',{}).get('MajorYN',self.config)
        self.identity={'panel_model':self.config.get('panel_model','unknown'),
                       'springback_deg':math.degrees(gains['yield_torque_nm']/gains['stiffness_nm_rad']),
                       'tip_force_to_crease_n':gains['yield_torque_nm']/(self.config['width_m']/2-self.config.get('flap_tip_clearance_m',0))}
        print('Live carton attached; press Play. Evidence:',self.out)
        # Which asset is loaded is visible at a glance: the old strip asset springs back
        # by 43 degrees, the rigid-panel one by about 4.
        print('Loaded asset: %s, springback %.1f deg, %.3f N at the flap edge to crease it'%(
            self.identity['panel_model'],self.identity['springback_deg'],self.identity['tip_force_to_crease_n']))
        if self.identity['springback_deg']>15:print('WARNING: this is an old asset. A flap pushed shut will spring open again.')

    def _log(self,event):
        with (self.out/'events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')

    def _reset(self,*args):
        from parcel_forge.carton_lifecycle import release_view
        release_view(self.view)
        self.view=None;self.states={};self.pulses={};self.elapsed=0.;self.last_targets=None;self.bend_states={}
        self._log({'event':'timeline_stopped','plastic_history_reset_to_initial_asset':True})

    def push(self,flap,torque_nm=.08,seconds=.2):
        if self.config.get('interaction_mode')=='external_forces_only':raise ValueError('This asset accepts external physical forces; no drive-offset actuator')
        name=flap if flap.startswith('Hinge') else 'Hinge'+flap
        if name not in self.joints or not math.isfinite(torque_nm) or not math.isfinite(seconds) or seconds<=0:raise ValueError('invalid flap or finite torque/duration')
        self.pulses[name]=(float(torque_nm),self.elapsed+seconds)
        self._log({'event':'torque_pulse','joint':name,'torque_nm':torque_nm,'duration_s':seconds})

    def _step(self,dt,context):
        if self.failed or self.closed:return
        try:
            import omni.usd
            if omni.usd.get_context().get_stage()!=self.stage:raise RuntimeError('Stage changed; close this controller and attach to new asset')
            if self.view is None:
                from isaacsim.core.experimental.prims import Articulation
                self.view=Articulation('/World/Carton');self.names=self.view.dof_names
                if set(self.names)!=set(self.joints)|set(self.bends):raise RuntimeError('four-flap DOF mismatch')
                self.states={n:CreaseState(self.initial[n],0) for n in self.joints}
                self.bend_states={n:CreaseState(self.bend_initial[n],0) for n in self.bends}
                from parcel_forge.carton_mouse_diagnostic import diagnose
                self._log({'event':'physics_callback_initialized','dof_names':self.names,'mouse_diagnostic':diagnose()})
            angles=self.view.get_dof_positions().numpy()[0];velocities=self.view.get_dof_velocities().numpy()[0];targets=[];readbacks=[]
            c=self.config
            for i,name in enumerate(self.names):
                if name in self.bends:
                    k=self.bends[name]['stiffness_nm_rad'];state=self.bend_states[name]
                    if c.get('panel_constitutive_model')=='estimated_elastoplastic_strip_v1':
                        state,info=advance(state,float(angles[i]),float(dt),k,self.bends[name]['yield_torque_nm'],k*c['panel_plastic_time_s'],0.)
                        self.bend_states[name]=state
                        if info['plastic_increment_rad']!=0:self.stage.GetPrimAtPath('/World/Carton/'+name).GetAttribute('drive:angular:physics:targetPosition').Set(math.degrees(state.target))
                    targets.append(state.target);readbacks.append({'joint':name,'angle_rad':float(angles[i]),'velocity_rad_s':float(velocities[i]),'plastic_target_rad':state.target,'role':'panel_bend'});continue
                gains=c.get('crease_gains',{}).get(name.replace('Hinge',''),c)
                state,info=advance(self.states[name],float(angles[i]),float(dt),gains['stiffness_nm_rad'],gains['yield_torque_nm'],gains['plastic_viscosity_nm_s_rad'],c['softening_rate_per_rad']);self.states[name]=state
                pulse=self.pulses.get(name);torque=pulse[0] if pulse and self.elapsed<pulse[1] else 0.
                targets.append(state.target+torque/gains['stiffness_nm_rad'])
                if info['plastic_increment_rad']!=0:self.joints[name].GetTargetPositionAttr().Set(math.degrees(state.target))
                readbacks.append({'joint':name,'angle_rad':float(angles[i]),'velocity_rad_s':float(velocities[i]),'plastic_target_rad':state.target,'yield_torque_nm':info['yield_torque_nm'],'applied_torque_nm':torque})
            if targets!=self.last_targets:self.view.set_dof_position_targets([targets]);self.last_targets=targets
            self.elapsed+=float(dt);self.samples+=1
            if self.samples%8==0:self._log({'event':'readback','elapsed_s':self.elapsed,'flaps':readbacks})
        except Exception as exc:
            self.failed=True;self._log({'event':'failed','error':str(exc)});print('Live carton callback failed:',exc)

    def mouse_mode(self,mode):
        """force: SETTING_MOUSE_GRAB_WITH_FORCE, scaled by /physics/pickingForce.

        The joint-drag mode is gone: with that flag off the grab took hold of the whole
        carton instead of the flap the user was pointing at, which is useless here.
        """
        import carb
        if mode not in ['grab','force','push']:raise ValueError('mode must be force, grab or push')
        settings=carb.settings.get_settings();settings.set_bool('/physics/mouseInteractionEnabled',True)
        settings.set_bool('/physics/mouseGrab',mode!='push');settings.set_bool('/physics/forceGrab',True)
        self._log({'event':'mouse_mode_requested','mode':mode,'force_grab':mode in ('grab','force'),'human_mouse_interaction':'not_tested'})
        print(mode,': Play, then Shift + left mouse near the OUTER EDGE of a flap')

    def grab_strength(self,value=None):
        """Read or set /physics/pickingForce in this application.

        The installed package does not document what one unit of this setting is worth
        in newtons, so the working value has to be found by pulling. The default is 1.0
        and NVIDIA's own Kapla Arena demo raises it to 10 to move stacked blocks.
        This changes a setting in the running app only: nothing is installed or restarted.
        """
        import carb
        settings=carb.settings.get_settings();previous=settings.get('/physics/pickingForce')
        if value is None:return {'picking_force':previous,'force_needed_n':self.force_needed()}
        if not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError('grab strength must be positive and finite')
        settings.set_float('/physics/pickingForce',float(value))
        self._log({'event':'picking_force_changed','previous':previous,'new':float(value),'scope':'running application setting only','human_mouse_interaction':'not_tested'})
        print('pickingForce',previous,'->',value,'; restore with pf_live.grab_strength(%r)'%previous)
        return {'picking_force':settings.get('/physics/pickingForce'),'previous':previous}

    def mouse_no_shift(self,enabled=True):
        """Ask the installed physx UI to stop requiring Shift for a physics drag.

        This calls the extension's own public override; it does not enable, install or
        restart anything, and it does nothing if that extension is not running.
        """
        from parcel_forge.carton_mouse_diagnostic import _instance
        instance=_instance()
        if instance is None or isinstance(instance,Exception):
            self._log({'event':'mouse_override_unavailable','reason':str(instance)})
            print('The physx UI extension is not running here, so Shift cannot be overridden.');return False
        from omni.physxui.scripts.physxViewportOverlays import PhysxUIMouseInteraction
        instance.mouse_interaction_override_toggle(PhysxUIMouseInteraction.ENABLED if enabled else PhysxUIMouseInteraction.DEFAULT)
        self._log({'event':'mouse_shift_override',"enabled":bool(enabled),'human_mouse_interaction':'not_tested'})
        print('Physics drag without Shift:',enabled,'; plain left-drag now grabs while playing.')
        return True

    def force_needed(self):
        from parcel_forge.carton_feel import grab_force_table
        return grab_force_table(self.config)

    def show_controls(self):
        import omni.ui as ui
        if self.closed:raise RuntimeError('Controller closed; reload the parcel-forge editor script first')
        if self.window:
            self.window.visible=True
            return
        self.window=ui.Window('Parcel Forge - Live carton',width=520,height=460)
        with self.window.frame:
            with ui.VStack(spacing=5):
                ui.Label('Play timeline; Shift + left mouse on a major flap')
                with ui.HStack():
                    ui.Button('Mouse: drag',clicked_fn=lambda:self.mouse_mode('force'))
                    ui.Button('Mouse: push',clicked_fn=lambda:self.mouse_mode('push'))
                with ui.HStack():
                    ui.Label('Grab strength (/physics/pickingForce)',width=250)
                    strength=ui.SimpleFloatModel(float(self.grab_strength()['picking_force'] or 1.))
                    strength.add_value_changed_fn(lambda m:m.as_float>0 and self.grab_strength(m.as_float))
                    ui.FloatDrag(strength,min=.5,max=200,step=.5)
                table=self.force_needed()
                ui.Label('This flap needs %.2f N at its outer edge, %.2f N grabbed halfway.'%(
                    table['by_grab_point'][0]['force_n'],table['by_grab_point'][2]['force_n']))
                ui.Label('Positive pulls the flap open, negative presses it shut, 0 lets go.')
                ui.Label('Flap angle: 0 shut, 90 upright, 180 out like a shelf, 270 folded down the wall.')
                # The probe stays available to scripts and tests; its four sliders are
                # gone from the window because the mouse is the way this is handled now.
                from parcel_forge.carton_force_probe import ForceProbe
                self.force_probe=ForceProbe(self.config,self.out)
                ui.Label('Drag a flap with the mouse. No open/closed state commands exist.')
                ui.Label('Directional strip panels' if self.bends else 'Rigid panels / fixed base. Not calibrated cardboard.')
        self.mouse_mode('force')

    def close(self):
        self.closed=True
        if self.force_probe:self.force_probe.close();self.force_probe=None
        for uid in self.ids:self.manager.deregister_callback(uid)
        self.ids=[]
        if self.window:self.window.destroy();self.window=None
        self._log({'event':'controller_detached','samples':self.samples,'failed':self.failed,'human_mouse_interaction':'not_tested'})
        from parcel_forge.carton_lifecycle import release_controller_references
        release_controller_references(self)
        print('Detached only parcel-forge callbacks; USD references released')

def attach(run='20260917T114330Z_ext1_carton',show_ui=True):
    root=Path(__file__).resolve().parents[2];source=(root/'runs'/run).resolve()
    if source.parent!=root/'runs':raise ValueError('run must be direct runs child')
    controller=LiveCarton(json.loads((source/'config.json').read_text()))
    if show_ui:controller.show_controls()
    return controller
