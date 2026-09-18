"""Cold-load portable generated USD in a fresh Isaac process; measure movement."""
import argparse,json,math
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);runtime=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);view=None;result={'status':'fail','cold_live_execution':'not_tested','physics_execution':'not_tested','state_readback':'not_tested','render':'not_tested','human_webrtc':'not_tested'}
 try:
  runtime.start()
  import omni.usd
  from pxr import UsdPhysics,UsdGeom
  if not omni.usd.get_context().open_stage(str(out/'scene.usda')):raise RuntimeError('cold open_stage failed')
  runtime.stage=omni.usd.get_context().get_stage();body=runtime.stage.GetPrimAtPath('/World/Drill');valid=bool(body and body.HasAPI(UsdPhysics.RigidBodyAPI));result['runtime']=runtime.configure_physics(gravity=9.81,enable_ccd=True);runtime.play();runtime.step(8);view=runtime.rigid_view('/World/Drill');finite=True
  for i in range(600):
   runtime.step()
   if i%20==0:finite=finite and runtime.is_finite(runtime.read_state(view))
  before=runtime.read_state(view)
  for i in range(48):view.apply_forces_and_torques_at_pos(forces=[[15.,0,0]]);runtime.step();finite=finite and runtime.is_finite(runtime.read_state(view))
  after=runtime.read_state(view);displacement=math.dist(before['position_m'][:2],after['position_m'][:2]);checks={'cold_rigid_present':valid,'finite_states':finite,'moves_under_external_force':displacement>.002,'lands_above_ground':before['position_m'][2]>0,'settles_before_push':sum(v*v for v in before['linear_velocity_mps'])**.5<.02};result.update(status='pass' if all(checks.values()) else 'fail',cold_live_execution='pass' if all(checks.values()) else 'fail',physics_execution='pass' if all(checks.values()) else 'fail',state_readback='pass',checks=checks,before=before,after=after,horizontal_displacement_m=displacement,mass_readback=view.get_masses().numpy().tolist())
 except Exception as e:result['error']=repr(e);raise
 finally:
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  if view is not None:
   from parcel_forge.carton_lifecycle import release_view
   release_view(view)
  runtime.close()
 return 0 if result['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
