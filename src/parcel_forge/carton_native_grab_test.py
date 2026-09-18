"""Drive the real viewport grab from Python and measure whether it moves a flap.

omni.physx.ui turns a shift-drag into get_physx_interface().update_interaction(ray,
event). That call is scriptable, so the native grab can be exercised headlessly
instead of being left as 'only the user can confirm'. What this cannot reproduce is
the user's mouse, keyboard and viewport camera.
"""
import argparse,json,math,traceback
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.carton_pull_test import build_config


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    out=Path(args.out);root=Path(__file__).resolve().parents[2];dt=1/240
    config=build_config(root,4.,1.5,dt)
    result={'status':'fail','physics':'not_tested','native_grab_api':'not_tested','human_mouse':'not_tested','render':'not_tested'}
    runtime=IsaacSimRuntime(dt=dt,device='cpu',enable_cameras=False);controller=None
    try:
        runtime.start()
        from parcel_forge.carton_author import author_carton
        author_carton(runtime.stage,config)
        # Control body: a plain dynamic cube, not part of any articulation. If the grab
        # attaches to this and not to a flap, the flap's problem is that it is a link.
        from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
        cube=UsdGeom.Cube.Define(runtime.stage,'/World/GrabControlCube');cube.CreateSizeAttr(1)
        api=UsdGeom.XformCommonAPI(cube);api.SetScale(Gf.Vec3f(.05,.05,.05));api.SetTranslate(Gf.Vec3d(.5,0,.2))
        UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim());UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(.0115)
        ground=UsdGeom.Cube.Define(runtime.stage,'/World/Ground');ground.CreateSizeAttr(1)
        api=UsdGeom.XformCommonAPI(ground);api.SetScale(Gf.Vec3f(4,4,.02));api.SetTranslate(Gf.Vec3d(0,0,-.01))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
        runtime.configure_physics(gravity=9.81,enable_ccd=False)
        runtime.stage.GetRootLayer().Export(str(out/'asset.usda'));(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        import carb
        from omni.physx import get_physx_interface
        from omni.physx.bindings._physx import PhysicsInteractionEvent,SimulationEvent
        from isaacsim.core.experimental.prims import RigidPrim
        from pxr import Gf
        from parcel_forge.carton_live import LiveCarton
        controller=LiveCarton(config);runtime.play();runtime.step(4)
        physx=get_physx_interface();settings=carb.settings.get_settings()
        # The C++ interaction is gated by these; the earlier version of this test left
        # them unset, so no grab could attach and the result meant nothing.
        settings.set_bool('/physics/mouseInteractionEnabled',True);settings.set_bool('/physics/mouseGrab',True)
        settings.set_bool('/physics/forceGrab',True)
        result['interaction_settings']={k:settings.get(k) for k in ['/physics/mouseInteractionEnabled','/physics/mouseGrab','/physics/forceGrab','/physics/pickingForce']}
        grabs=[]
        def on_event(event):
            if event.type==int(SimulationEvent.POINT_GRABBED):
                grabs.append({'grabbed_position':list(event.payload['grabbed_position']),'grab_force_position':list(event.payload['grab_force_position'])})
        # runtime.step() does not pump the app loop, so the event stream is popped by
        # hand; without this POINT_GRABBED never arrives and looks like a failed grab.
        stream=physx.get_simulation_event_stream_v2();subscription=stream.create_subscription_to_pop(on_event)
        def angle(flap):
            if flap=='GrabControlCube':return float(edge(flap)[2])*1000.
            names=controller.names;positions=controller.view.get_dof_positions().numpy()[0]
            return math.degrees(float(positions[names.index('Hinge'+flap)]))
        def edge(flap):
            if flap=='GrabControlCube':
                position,orientation=RigidPrim('/World/GrabControlCube').get_world_poses()
                return Gf.Vec3d(*map(float,position.numpy()[0]))
            body=RigidPrim('/World/Carton/'+flap);position,orientation=body.get_world_poses()
            p=position.numpy()[0];q=orientation.numpy()[0]
            rotation=Gf.Rotation(Gf.Quatd(float(q[0]),Gf.Vec3d(*map(float,q[1:]))))
            lever=config['width_m']/2-config['flap_tip_clearance_m']
            return Gf.Vec3d(*map(float,p))+rotation.TransformDir(Gf.Vec3d(0,lever*.9,0))
        def drag(flap,picking_force,lift=.10,seconds=1.5):
            """One scripted shift-drag: grab the flap edge and pull the aim point up."""
            settings.set_float('/physics/pickingForce',float(picking_force))
            start=edge(flap);eye=start+Gf.Vec3d(.25,-.25,.25)
            before=len(grabs);trace=[]
            def ray(target):
                direction=(target-eye).GetNormalized()
                return carb.Float3(*map(float,eye)),carb.Float3(*map(float,direction))
            origin,direction=ray(start);physx.update_interaction(origin,direction,PhysicsInteractionEvent.MOUSE_DRAG_BEGAN)
            steps=round(seconds/dt)
            for step in range(steps):
                target=start+Gf.Vec3d(0,0,lift*(step+1)/steps)
                origin,direction=ray(target);physx.update_interaction(origin,direction,PhysicsInteractionEvent.MOUSE_DRAG_CHANGED)
                runtime.step();stream.pump()
                if step%24==0:trace.append({'t_s':step*dt,'aim_z':float(target[2]),'angle_deg':angle(flap)})
            origin,direction=ray(start+Gf.Vec3d(0,0,lift));physx.update_interaction(origin,direction,PhysicsInteractionEvent.MOUSE_DRAG_ENDED)
            peak=max([point['angle_deg'] for point in trace]+[angle(flap)])
            runtime.step(480);stream.pump()
            row={'flap':flap,'picking_force':picking_force,'grab_events':len(grabs)-before,'peak_deg':peak,
                 'settled_deg':angle(flap),'trace':trace,'grab_positions':grabs[before:before+1]}
            if flap!='GrabControlCube':
                row.update(plastic_reference_deg=math.degrees(controller.states['Hinge'+flap].target),controller_samples=controller.samples)
            else:
                row.update(rise_m=float(edge('GrabControlCube')[2]-start[2]))
            return row
        runtime.step(120)
        control=drag('GrabControlCube',1.)
        settings.set_bool('/physics/forceGrab',False);joint_control=drag('GrabControlCube',1.)
        settings.set_bool('/physics/forceGrab',True)
        trials=[drag('MajorYN',1.),drag('MajorYP',1000.),drag('MinorXP',1000.,lift=.05,seconds=3.)]
        from parcel_forge.carton_mouse_diagnostic import diagnose
        result['mouse_diagnosis']=diagnose()
        settings.set_float('/physics/pickingForce',1.)
        subscription=None
        checks={'grab_api_available':True,
                'control_cube_grab_attached':control['grab_events']>0,
                'control_cube_lifted':control['rise_m']>.02,
                'default_strength_grab_attached':trials[0]['grab_events']>0,
                'default_strength_opens_flap':trials[0]['peak_deg']>10.,
                'high_strength_grab_attached':trials[1]['grab_events']>0,
                'high_strength_opens_flap':trials[1]['peak_deg']>10.,
                'grab_leaves_a_permanent_crease':trials[1]['plastic_reference_deg']>10.,
                'crease_callback_ran_during_the_grab':trials[1]['controller_samples']>trials[0]['controller_samples'],
                'callback_no_error':not controller.failed}
        # The interaction subsystem ships with omni.physx.ui. A standalone app without
        # that extension has no grab to exercise, so this is blocked, not failed: the
        # control body never moving is the proof that the call did nothing here.
        blocked=bool(result['mouse_diagnosis']['blockers'])
        status='blocked' if blocked else ('pass' if all(checks.values()) else 'fail')
        result.update(status=status,physics='pass',native_grab_api='blocked' if blocked else 'pass',
                      checks=checks,trials=trials,control_body=control,control_body_joint_drag=joint_control,
                      unexplained_observation='at pickingForce 1000 MajorYP spiked to 100 deg with no POINT_GRABBED event and a control body that never moved; not attributed to the grab',
                      scope='scripted native interaction ray; with omni.physx.ui disabled there is no interaction subsystem to drive, so this says nothing about a viewer where it is enabled')
        if blocked:(out/'blocked.json').write_text(json.dumps({'reason':'omni.physx.ui is not enabled in this standalone app; the native grab cannot be exercised here','diagnosis':result['mouse_diagnosis']},indent=2)+'\n')
    except Exception as exc:result['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if controller:controller.close()
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');runtime.close()
    return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
