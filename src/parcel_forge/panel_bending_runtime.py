"""Isolated MD/CD end-couple benchmark and segmented carton export."""
import argparse,json,math,traceback,csv
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.panel_bending import stiffness,add_joint,author_segmented_carton

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);root=Path(__file__).resolve().parents[2]
    material=json.loads((root/'config/materials/b_flute_130tl.json').read_text());r=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False)
    report={'status':'fail','render':'not_tested','webrtc_human_view':'not_tested','model':'1D segmented strip, not full orthotropic shell'}
    try:
        r.start()
        from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
        from isaacsim.core.experimental.prims import Articulation,RigidPrim
        stage=r.stage;UsdGeom.Xform.Define(stage,'/World');stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
        L,b,n,M=.2,.05,8,.03;h=L/n;views={};ks={}
        for direction,y in [('MD',-.08),('CD',.08)]:
            base='/World/'+direction;prim=UsdGeom.Xform.Define(stage,base).GetPrim();UsdPhysics.ArticulationRootAPI.Apply(prim);api=PhysxSchema.PhysxArticulationAPI.Apply(prim);api.CreateEnabledSelfCollisionsAttr(True);api.CreateSolverPositionIterationCountAttr(64);api.CreateSolverVelocityIterationCountAttr(8)
            anchor=UsdGeom.Xform.Define(stage,base+'/Anchor');UsdGeom.XformCommonAPI(anchor).SetTranslate(Gf.Vec3d(0,y,.2));UsdPhysics.RigidBodyAPI.Apply(anchor.GetPrim());UsdPhysics.MassAPI.Apply(anchor.GetPrim()).CreateMassAttr(.1)
            fixed=UsdPhysics.FixedJoint.Define(stage,base+'/Fixed');fixed.CreateBody1Rel().SetTargets([anchor.GetPath()]);prev=str(anchor.GetPath());ks[direction]=[]
            for i in range(n):
                path=base+'/S'+str(i);link=UsdGeom.Xform.Define(stage,path);UsdGeom.XformCommonAPI(link).SetTranslate(Gf.Vec3d(i*h,y,.2));UsdPhysics.RigidBodyAPI.Apply(link.GetPrim());UsdPhysics.MassAPI.Apply(link.GetPrim()).CreateMassAttr(material['areal_mass_kg_m2']*b*h)
                cube=UsdGeom.Cube.Define(stage,path+'/Panel');cube.CreateSizeAttr(1);x=UsdGeom.XformCommonAPI(cube);x.SetScale(Gf.Vec3f(h,b,material['thickness_m']));x.SetTranslate(Gf.Vec3d(h/2,0,0));cube.CreateDisplayColorAttr([Gf.Vec3f(.65,.4,.15)]);UsdPhysics.CollisionAPI.Apply(cube.GetPrim());PhysxSchema.PhysxCollisionAPI.Apply(cube.GetPrim()).CreateContactOffsetAttr(.0001)
                k=stiffness(material['bending_stiffness_nm'][direction],b,h,i==0);ks[direction].append(k)
                add_joint(stage,base+'/J'+str(i),prev,path,(0 if i==0 else h,0,0),k,'Y');prev=path
        r.configure_physics(gravity=0,enable_ccd=False);stage.GetRootLayer().Export(str(out/'coupon_asset.usda'));r.play();r.step(4)
        views={d:Articulation('/World/'+d) for d in ks};tips={d:RigidPrim('/World/'+d+'/S7') for d in ks};rows=[];measured={}
        def tip(d):
            pos,q=tips[d].get_world_poses();pos=pos.numpy()[0];q=q.numpy()[0];v=Gf.Rotation(Gf.Quatd(float(q[0]),Gf.Vec3d(*map(float,q[1:])))).TransformDir(Gf.Vec3d(h,0,0));return float(pos[2]+v[2]-.2)
        for step in range(1440):
            if step in (0,720):
                for d,v in views.items():v.set_dof_position_targets([[M/ks[d][int(name[1:])] if step==0 else 0 for name in v.dof_names]])
            r.step(1)
            if step%8==0:rows.append({'t_s':(step+1)/240,'MD_tip_z_m':tip('MD'),'CD_tip_z_m':tip('CD')})
            if step==719:
                for d in ks:
                    curvature=M/(material['bending_stiffness_nm'][d]*b);expected=-(1-math.cos(curvature*L))/curvature
                    measured[d]={'loaded_tip_z_m':tip(d),'analytic_tip_z_m':expected,'relative_error':abs(tip(d)-expected)/abs(expected)}
        for d in ks:measured[d]['released_tip_z_m']=tip(d)
        checks={'analytic_5_percent':all(x['relative_error']<.05 for x in measured.values()),'CD_more_flexible':abs(measured['CD']['loaded_tip_z_m'])>abs(measured['MD']['loaded_tip_z_m']),'elastic_return_0_1mm':all(abs(x['released_tip_z_m'])<.0001 for x in measured.values()),'finite':all(math.isfinite(v) for x in measured.values() for v in x.values())}
        with (out/'trajectory.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        report.update(status='pass' if all(checks.values()) else 'fail',checks=checks,measured=measured,loading='constant end couple, algebraically equivalent generalized torques M on each joint',gravity_m_s2=0)
        import omni.timeline
        omni.timeline.get_timeline_interface().stop();r.app.update();stage=r.stage;stage.RemovePrim("/World");UsdGeom.SetStageMetersPerUnit(stage,1);UsdGeom.SetStageUpAxis(stage,'Z')
        config=json.loads((root/'runs/20260917T114330Z_ext1_carton/config.json').read_text());config.update(thickness_m=material['thickness_m'],initial_angle_deg=0,panel_directions={'MajorYN':'CD','MajorYP':'CD','MinorXP':'MD','MinorXN':'MD'},material=material,panel_direction_provenance='assumed blank orientation; requires confirmation',panel_damping_provenance='numerical estimate, not measured')
        config['panel_stability_policy']='record';author_segmented_carton(stage,config,material);r.configure_physics(gravity=9.81,enable_ccd=False);stage.GetRootLayer().Export(str(out/'asset.usda'));(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        from parcel_forge.carton_live import LiveCarton
        controller=LiveCarton(config);r.play();r.step(4);controller.push('MajorYN',.08,3);controller.push('MajorYP',.08,3);r.step(960)
        report['carton_callback']={'samples':controller.samples,'failed':controller.failed,'dofs':len(controller.names)};controller.close()
        report['checks']['segmented_carton_live_readback']=not controller.failed and len(controller.names)==16 and controller.samples>900
        report['status']='pass' if all(report['checks'].values()) else 'fail'
    except Exception as exc:report['status']='fail';report['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');r.close()
if __name__=='__main__':main()
