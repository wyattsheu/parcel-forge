"""Robot-like kinematic fingertip acts by contact; carton has no action commands."""
import argparse,json,math,traceback,csv
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--source',required=True);a=p.parse_args();out=Path(a.out);source=Path(a.source)
    c=json.loads((source/'config.json').read_text());r=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);controller=None;report={'status':'fail','native_mouse':'not_tested','actual_robot':'not_tested','render':'not_tested'}
    try:
        r.start()
        from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf
        from isaacsim.core.experimental.prims import RigidPrim
        loaded=Usd.Stage.Open(str(source/'asset.usda'));r.stage.GetRootLayer().TransferContent(loaded.GetRootLayer());r.configure_physics(gravity=9.81,enable_ccd=False)
        finger=UsdGeom.Sphere.Define(r.stage,'/World/TestFinger');finger.CreateRadiusAttr(.009);UsdGeom.XformCommonAPI(finger).SetTranslate(Gf.Vec3d(0,-.025,.13));UsdPhysics.CollisionAPI.Apply(finger.GetPrim());body=UsdPhysics.RigidBodyAPI.Apply(finger.GetPrim());body.CreateKinematicEnabledAttr(True);PhysxSchema.PhysxContactReportAPI.Apply(finger.GetPrim()).CreateThresholdAttr(0.);UsdPhysics.MassAPI.Apply(finger.GetPrim()).CreateMassAttr(1.)
        from parcel_forge.carton_live import LiveCarton
        controller=LiveCarton(c);r.play();r.step(4)
        import omni.physics.tensors as tensors
        import numpy as np
        import omni.usd
        sim=tensors.create_simulation_view('numpy',stage_id=omni.usd.get_context().get_stage_id());kin=sim.create_rigid_body_view('/World/TestFinger')
        tool=RigidPrim('/World/TestFinger',contact_filter_paths=['/World/Carton/MajorYN_S3'],max_contact_count=64);rows=[];contact_peak=0.;angle_peak=0.;other_peak=0.
        for i in range(600):
            if i<120:y,z=-.025,.13+(.15417-.01-.13)*(i/120)
            else:
                theta=min(1.,(i-120)/360)*math.radians(95);s=.075;radius=.009
                y=-.1+s*math.cos(theta)+(radius+.0005)*math.sin(theta);z=.15+1.5*c['thickness_m']+s*math.sin(theta)-(radius+.0005)*math.cos(theta)
            kin.set_kinematic_targets(np.array([[0,y,z,0,0,0,1]],dtype=np.float32),np.array([0],dtype=np.uint32));r.step(1)
            values=dict(zip(controller.names,map(float,controller.view.get_dof_positions().numpy()[0])));contact=tool.get_net_contact_forces(dt=1/240).numpy()[0];norm=float(sum(float(v)**2 for v in contact)**.5)
            contact_peak=max(contact_peak,norm);angle_peak=max(angle_peak,values['HingeMajorYN']);other_peak=max(other_peak,abs(values['HingeMajorYP']))
            rows.append({'t_s':i/240,'finger_y_m':y,'finger_z_m':z,'major_angle_rad':values['HingeMajorYN'],'other_major_angle_rad':values['HingeMajorYP'],'contact_force_n':norm,'finger_readback_z_m':float(tool.get_world_poses()[0].numpy()[0][2])})
        checks={'contact_force_measured':contact_peak>.001,'one_major_opens_by_collision':angle_peak>.5,'opposite_major_stays_closed':other_peak<.1,'material_callback_no_error':not controller.failed,'no_action_commands':not controller.pulses and controller.force_probe is None}
        report.update(status='pass' if all(checks.values()) else 'fail',checks=checks,peak_contact_force_n=contact_peak,peak_major_angle_rad=angle_peak,peak_opposite_major_abs_rad=other_peak,callback_run=str(controller.out),scope='kinematic spherical fingertip collision, no carton target/pose commands; not full robot/gripper workflow')
        with (out/'contact_trajectory.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    except Exception as exc:report['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if controller:controller.close()
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');r.close()
if __name__=='__main__':main()
