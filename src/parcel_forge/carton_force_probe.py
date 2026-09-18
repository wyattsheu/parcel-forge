"""Optional external force test apparatus, separate from material constitutive law."""
import math,json
class ForceProbe:
    def __init__(self,config,out):
        from isaacsim.core.simulation_manager import SimulationManager,SimulationEvent
        import omni.usd
        self.stage=omni.usd.get_context().get_stage()
        self.config=config;self.out=out;self.loads={};self.views={};self.elapsed=0.;self.models=[];self.failed=False
        self.manager=SimulationManager;self.ids=[SimulationManager.register_callback(self._step,SimulationEvent.PHYSICS_PRE_STEP),SimulationManager.register_callback(self._reset,SimulationEvent.SIMULATION_STOPPED)]
    def _log(self,event):
        with (self.out/'force_probe.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
    def _reset(self,*args):
        from parcel_forge.carton_lifecycle import release_view
        for view in self.views.values():release_view(view)
        self.loads={};self.views={};self.elapsed=0.
    def apply(self,flap,force_n,seconds=None,fraction=1.):
        if flap not in ['MajorYN','MajorYP','MinorXP','MinorXN'] or not math.isfinite(force_n) or (seconds is not None and (not math.isfinite(seconds) or seconds<=0)):raise ValueError('invalid force/flap/duration')
        if not math.isfinite(fraction) or not 0<fraction<=1:raise ValueError('grab fraction must be in (0,1]')
        self.loads[flap]=(float(force_n),None if seconds is None else self.elapsed+seconds,float(fraction));self._log({'event':'edge_force','flap':flap,'force_n':force_n,'duration_s':seconds,'grab_fraction':fraction})
    def strike(self,flap,force_n=-10.,duration_s=.05):
        """Finite force pulse; nominal impulse F*duration, not imposed velocity."""
        if flap in ['MajorYN','MajorYP','MinorXP','MinorXN'] and self.models:self.models[['MajorYN','MajorYP','MinorXP','MinorXN'].index(flap)].set_value(0.)
        self.apply(flap,force_n,duration_s)
        self._log({'event':'strike','flap':flap,'force_n':force_n,'duration_s':duration_s,'nominal_impulse_ns':force_n*duration_s})
    def release(self):
        self.loads={}
        for model in self.models:model.set_value(0.)
        self._log({'event':'release_all'})
    def _step(self,dt,context):
        if self.failed:return
        try:
            import omni.usd
            if omni.usd.get_context().get_stage()!=self.stage:raise RuntimeError('force probe source stage changed')
            from isaacsim.core.experimental.prims import RigidPrim
            from pxr import Gf
            for flap,(force,end,fraction) in list(self.loads.items()):
                if end is not None and self.elapsed>=end:del self.loads[flap];continue
                if force==0:continue
                n=self.config.get('panel_segments',4) if self.config.get('panel_bend_joints') else 1
                path='/World/Carton/'+flap+('_S'+str(n-1) if n>1 else '')
                if flap not in self.views:self.views[flap]=RigidPrim(path)
                body=self.views[flap];pos,q=body.get_world_poses();pos=pos.numpy()[0];q=q.numpy()[0]
                rot=Gf.Rotation(Gf.Quatd(float(q[0]),Gf.Vec3d(*map(float,q[1:]))));h=(self.config['width_m']/2-self.config.get('flap_tip_clearance_m',0))/n
                edge=Gf.Vec3d(*map(float,pos))+rot.TransformDir(Gf.Vec3d(0,h*fraction,0));vector=rot.TransformDir(Gf.Vec3d(0,0,force))
                body.apply_forces_and_torques_at_pos(forces=[list(vector)],positions=[list(edge)])
            self.elapsed+=float(dt)
        except Exception as exc:self.failed=True;self._log({'event':'failed','error':str(exc)})
    def build_ui(self):
        import omni.ui as ui
        for name in ['MajorYN','MajorYP','MinorXP','MinorXN']:
            with ui.HStack():
                ui.Label(name+' edge force N',width=180);model=ui.SimpleFloatModel(0.);self.models.append(model)
                model.add_value_changed_fn(lambda m,n=name:self.apply(n,m.as_float));ui.FloatDrag(model,min=-50,max=50,step=.25)
                ui.Button('Hit 10N / 0.05s',clicked_fn=lambda n=name:self.strike(n))
        ui.Button('Release test forces',clicked_fn=self.release)
        ui.Label('Positive = pull, negative = press (current panel normal).')
        ui.Label('Hit = short force pulse. Continuous force ends at zero/release.')
        ui.Label('Native Shift-drag is separate and remains unverified.')
    def close(self):
        from parcel_forge.carton_lifecycle import release_view
        self.loads={}
        for view in self.views.values():release_view(view)
        self.views={};self.stage=None;self.models=[]
        for uid in self.ids:self.manager.deregister_callback(uid)
        self.ids=[];self._log({'event':'probe_closed','failed':self.failed})
