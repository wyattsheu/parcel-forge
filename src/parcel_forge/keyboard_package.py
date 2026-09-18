"""One representative package fixture; passive carton and rigid keyboard proxy."""
import argparse,json,math
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=Path(args.out)
    runtime=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);controller=None;keyboard=None;base=None
    result={'status':'fail','physics_execution':'not_tested','render':'not_tested','human_webrtc':'not_tested','calibration':'not_tested','scope':'free-base carton with rigid keyboard proxy; no key actuation or robot grasp'}
    try:
        runtime.start()
        from pxr import UsdGeom,UsdPhysics,Gf
        from parcel_forge.carton_pull_test import build_config,board_mass
        from parcel_forge.carton_feel import derive_carton_creases
        from parcel_forge.carton_author import author_carton
        root=Path(__file__).resolve().parents[2]
        config=build_config(root,4.,1.5,1/240,'free')
        config.update(length_m=.48,width_m=.22,height_m=.12)
        config['base_mass_kg']=board_mass(config);config.update(derive_carton_creases(config,4.,1.5))
        author_carton(runtime.stage,config)
        stage=runtime.stage;body=UsdGeom.Xform.Define(stage,'/World/Keyboard')
        UsdGeom.XformCommonAPI(body).SetTranslate(Gf.Vec3d(0,0,.03))
        UsdPhysics.RigidBodyAPI.Apply(body.GetPrim());UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(.65)
        def plate(path,size,position,color,collision=False):
            cube=UsdGeom.Cube.Define(stage,path);cube.CreateSizeAttr(1)
            transform=UsdGeom.XformCommonAPI(cube);transform.SetTranslate(Gf.Vec3d(*position));transform.SetScale(Gf.Vec3f(*size))
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
            if collision:UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        plate('/World/Keyboard/Case',(.43,.145,.022),(0,0,0),(.09,.10,.12),True)
        for row in range(5):
            for column in range(18):
                plate(f'/World/Keyboard/Key_{row}_{column}',(.018,.019,.005),(-.20+column*.023,-.05+row*.024,.0135),(.65,.65,.67))
        world_anchors=[]
        for prim in stage.Traverse():
            if prim.IsA(UsdPhysics.Joint):
                joint=UsdPhysics.Joint(prim)
                if not joint.GetBody0Rel().GetTargets() or not joint.GetBody1Rel().GetTargets():world_anchors.append(str(prim.GetPath()))
        (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        stage.GetRootLayer().Export(str(out/'asset.usda'))
        result['runtime']=runtime.configure_physics(gravity=9.81,enable_ccd=False)
        from parcel_forge.carton_live import LiveCarton
        from isaacsim.core.experimental.prims import RigidPrim
        controller=LiveCarton(config);controller.show_controls();runtime.play();runtime.step(8)
        keyboard=RigidPrim('/World/Keyboard');base=RigidPrim('/World/Carton/Base');trajectory=[]
        def sample(phase):
            poses=keyboard.get_world_poses()[0].numpy()[0].tolist()
            angles={n:math.degrees(float(v)) for n,v in zip(controller.names,controller.view.get_dof_positions().numpy()[0])}
            base_pos,base_q=base.get_world_poses();bp=base_pos.numpy()[0].tolist();q=base_q.numpy()[0].tolist()
            rotation=Gf.Rotation(Gf.Quatd(q[0],Gf.Vec3d(*q[1:])))
            local=list(rotation.GetInverse().TransformDir(Gf.Vec3d(*poses)-Gf.Vec3d(*bp)))
            trajectory.append({'phase':phase,'keyboard_position':poses,'base_position':bp,'keyboard_in_base':local,'angles_deg':angles});return poses,angles
        runtime.step(360);initial,_=sample('settled')
        for flap in ('MajorYP','MajorYN','MinorXP','MinorXN'):
            controller.force_probe.apply(flap,.6,.6)
            runtime.step(144);controller.force_probe.release();runtime.step(180);sample('released_'+flap)
        final,angles=sample('final')
        opening_local=trajectory[-1]['keyboard_in_base']
        before=base.get_world_poses()[0].numpy()[0].tolist()
        # External test force only; no pose/velocity commands and no fixture joint.
        for _ in range(48):
            base.apply_forces_and_torques_at_pos(forces=[[12.,0,0]])
            runtime.step()
        after=base.get_world_poses()[0].numpy()[0].tolist();sample('after_horizontal_push')
        mobility=math.dist(before[:2],after[:2])
        checks={'no_world_anchor':not world_anchors,'base_dynamic':bool(UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath('/World/Carton/Base')).GetRigidBodyEnabledAttr().Get()),
                'box_moves_under_external_force':mobility>.002,
                'finite_readback':all(math.isfinite(v) for row in trajectory for v in row['keyboard_position']+list(row['angles_deg'].values())),
                'keyboard_remains_inside':abs(opening_local[0])<(.48-.43)/2 and abs(opening_local[1])<(.22-.145)/2 and .01<opening_local[2]<.08,
                'four_flaps_open_by_external_force':all(v>60 for v in angles.values()),
                'callback_no_error':not controller.failed if hasattr(controller,'failed') else not controller.force_probe.failed}
        result.update(checks=checks,physics_execution='pass' if all(checks.values()) else 'fail',status='pass' if all(checks.values()) else 'fail',trajectory=trajectory,
                      initial_keyboard_position=initial,final_keyboard_position=final,keyboard_mass_readback=keyboard.get_masses().numpy().tolist(),
                      extraction='not_tested',keyboard_collision='single rigid case; keycaps visual only',base_boundary='free dynamic body, ground contact only',world_anchors=world_anchors,
                      mobility={'force_n':[12.,0,0],'duration_s':.2,'before':before,'after':after,'horizontal_displacement_m':mobility,'minimum_displacement_m':.002},
                      mobility_verified=True)
        stage.GetRootLayer().Export(str(out/'scene_final.usda'))
    except Exception as exc:
        result['error']=repr(exc);raise
    finally:
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        if controller is not None:controller.close()
        from parcel_forge.carton_lifecycle import release_view
        for view in (keyboard,base):
            if view is not None:release_view(view)
        runtime.close()
    return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
