"""Author generated OBJ into portable USD and measure a free dynamic body in Isaac."""
import argparse,json,math
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.workflow.image_intake import obj_info

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);spec=json.loads((out/'config.json').read_text());runtime=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);view=None
 result={'status':'fail','physics_execution':'not_tested','state_readback':'not_tested','headless':'not_tested','render':'not_tested','human_webrtc':'not_tested','calibration':'not_tested','shape_fidelity':'not_tested','contact_fidelity':'not_tested'}
 try:
  runtime.start()
  from pxr import Usd,UsdGeom,UsdPhysics,UsdLux,UsdShade,PhysxSchema,Gf,Sdf
  import numpy as np
  mesh_path=out/'input/mesh.obj';metrics=obj_info(mesh_path);points=[];colors=[];faces=[]
  for line in mesh_path.read_text().splitlines():
   f=line.split('#',1)[0].split()
   if not f:continue
   if f[0]=='v':
    points.append([float(x) for x in f[1:4]]);colors.append([float(x) for x in f[4:7]] if len(f)==7 else [.55,.55,.55])
   elif f[0]=='f':faces.append([int(x.split('/')[0])-1 if int(x.split('/')[0])>0 else len(points)+int(x.split('/')[0]) for x in f[1:]])
  low=np.array(metrics['bbox_min_native']);high=np.array(metrics['bbox_max_native']);center=(low+high)/2;scale=spec['length_m']/max(metrics['extent_native']);pts=(np.array(points)-center)*scale;extent=(high-low)*scale
  asset=Usd.Stage.CreateNew(str(out/'asset.usda'));UsdGeom.SetStageMetersPerUnit(asset,1.);UsdGeom.SetStageUpAxis(asset,'Z');UsdPhysics.SetStageKilogramsPerUnit(asset,1.)
  body=UsdGeom.Xform.Define(asset,'/Drill');asset.SetDefaultPrim(body.GetPrim());Usd.ModelAPI(body.GetPrim()).SetKind('component');UsdPhysics.RigidBodyAPI.Apply(body.GetPrim());mass=UsdPhysics.MassAPI.Apply(body.GetPrim());mass.CreateMassAttr(spec['mass_kg']);PhysxSchema.PhysxRigidBodyAPI.Apply(body.GetPrim()).CreateEnableCCDAttr(True)
  def surface(stage,path):
   m=UsdGeom.Mesh.Define(stage,path);m.CreatePointsAttr([Gf.Vec3f(*row) for row in pts]);m.CreateFaceVertexCountsAttr([len(f) for f in faces]);m.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);m.CreateSubdivisionSchemeAttr('none');m.CreateDoubleSidedAttr(True);m.CreateExtentAttr([Gf.Vec3f(*(-extent/2)),Gf.Vec3f(*(extent/2))]);return m
  from parcel_forge.image_mesh_cleanup import srgb_to_linear
  linear_colors=[[srgb_to_linear(c) for c in rgb] for rgb in colors]
  visual=surface(asset,'/Drill/Visual');visual.CreateDisplayColorPrimvar(UsdGeom.Tokens.vertex).Set([Gf.Vec3f(*c) for c in linear_colors])
  appearance=UsdShade.Material.Define(asset,'/Drill/Appearance');shader=UsdShade.Shader.Define(asset,'/Drill/Appearance/Surface');shader.CreateIdAttr('UsdPreviewSurface');shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.85);shader.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(0.)
  reader=UsdShade.Shader.Define(asset,'/Drill/Appearance/Color');reader.CreateIdAttr('UsdPrimvarReader_float3');reader.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('displayColor');reader.CreateOutput('result',Sdf.ValueTypeNames.Float3)
  shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).ConnectToSource(reader.ConnectableAPI(),'result');shader.CreateOutput('surface',Sdf.ValueTypeNames.Token);appearance.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface');UsdShade.MaterialBindingAPI.Apply(visual.GetPrim()).Bind(appearance)
  collision=surface(asset,'/Drill/Collision');collision.CreatePurposeAttr('guide');UsdPhysics.CollisionAPI.Apply(collision.GetPrim());UsdPhysics.MeshCollisionAPI.Apply(collision.GetPrim()).CreateApproximationAttr('convexDecomposition');PhysxSchema.PhysxCollisionAPI.Apply(collision.GetPrim()).CreateContactOffsetAttr(.001)
  material=UsdShade.Material.Define(asset,'/Drill/PhysicsMaterial');ma=UsdPhysics.MaterialAPI.Apply(material.GetPrim());ma.CreateStaticFrictionAttr(.5);ma.CreateDynamicFrictionAttr(.4);ma.CreateRestitutionAttr(.05);UsdShade.MaterialBindingAPI.Apply(collision.GetPrim()).Bind(material,materialPurpose='physics')
  asset.GetRootLayer().Save();del asset
  stage=runtime.stage;UsdGeom.Xform.Define(stage,'/World');body=UsdGeom.Xform.Define(stage,'/World/Drill');body.GetPrim().GetReferences().AddReference(str(out/'asset.usda'));spawn=float(extent[2]/2+.08);UsdGeom.XformCommonAPI(body).SetTranslate(Gf.Vec3d(0,0,spawn));runtime.add_ground_plane(size=3,visual_size=1.)
  light=UsdLux.DomeLight.Define(stage,'/World/Light');light.CreateIntensityAttr(1000.)
  runtime_info=runtime.configure_physics(gravity=9.81,enable_ccd=True);scene=PhysxSchema.PhysxSceneAPI(stage.GetPrimAtPath(runtime_info['physics_scene_path']));scene.CreateTimeStepsPerSecondAttr(240);scene.CreateEnableGPUDynamicsAttr(False)
  # Scene initial snapshot includes solver configuration before export; references relative to this layer.
  stage.GetRootLayer().Export(str(out/'scene.usda'))
  cold=Usd.Stage.Open(str(out/'scene.usda'));ref=cold.GetPrimAtPath('/World/Drill').GetReferences();ref.ClearReferences();ref.AddReference('asset.usda');cold.GetRootLayer().Save();cold_body=cold.GetPrimAtPath('/World/Drill');cold_metrics={'rigid_enabled':UsdPhysics.RigidBodyAPI(cold_body).GetRigidBodyEnabledAttr().Get(),'collision_approximation':UsdPhysics.MeshCollisionAPI(cold.GetPrimAtPath('/World/Drill/Collision')).GetApproximationAttr().Get(),'meters_per_unit':UsdGeom.GetStageMetersPerUnit(cold),'physics_dt_hz':PhysxSchema.PhysxSceneAPI(cold.GetPrimAtPath(runtime_info['physics_scene_path'])).GetTimeStepsPerSecondAttr().Get()};del cold
  runtime.play();runtime.step(8);view=runtime.rigid_view('/World/Drill');trajectory=[]
  def sample(phase):
   s=runtime.read_state(view);s.update(phase=phase,time_s=runtime.sim_time);trajectory.append(s);return s
  sample('initial');finite=True
  for i in range(600):
   runtime.step()
   if i%20==0:finite=finite and runtime.is_finite(sample('fall_and_settle'))
  settled=sample('settled');before=settled['position_m']
  for i in range(48):view.apply_forces_and_torques_at_pos(forces=[[15.,0,0]]);runtime.step();finite=finite and runtime.is_finite(sample('push'))
  after=sample('after_push');displacement=math.dist(before[:2],after['position_m'][:2]);runtime.step(240);final=sample('released');mass_rb=np.asarray(view.get_masses().numpy()).reshape(-1)[0];inertia=np.array(view.get_inertias().numpy()[0]).reshape(3,3);eigen=np.linalg.eigvalsh((inertia+inertia.T)/2)
  world_joints=[str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)];bbox=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_]).ComputeLocalBound(stage.GetPrimAtPath('/World/Drill/Visual')).GetRange();measured=[float(x) for x in bbox.GetSize()]
  checks={'finite_states':finite and all(runtime.is_finite(row) for row in trajectory),'no_world_anchor_or_joint':not world_joints,'rigid_dynamic_enabled':bool(cold_metrics['rigid_enabled']),'mass_matches_spec':abs(float(mass_rb)-spec['mass_kg'])<1e-5,'positive_feasible_inertia':bool(np.all(eigen>0) and 2*max(eigen)<=sum(eigen)+1e-6*sum(eigen)),'metric_scale_matches_spec':abs(max(measured)-spec['length_m'])<1e-5,'lands_above_ground':settled['position_m'][2]>0 and settled['position_m'][2]<spawn,'settles_before_push':np.linalg.norm(settled['linear_velocity_mps'])<.02,'moves_under_external_force':displacement>.002,'cold_file_physics_present':cold_metrics['collision_approximation']=='convexDecomposition' and cold_metrics['meters_per_unit']==1. and cold_metrics['physics_dt_hz']==240}
  checks={k:bool(v) for k,v in checks.items()}
  result.update(status='pass' if all(checks.values()) else 'fail',physics_execution='pass' if all(checks.values()) else 'fail',state_readback='pass',headless='pass',checks=checks,runtime=runtime_info,cold_file_readback=cold_metrics,cold_live_execution='not_tested',trajectory=trajectory,extent_m=measured,scale_native_to_m=scale,mass_readback_kg=float(mass_rb),inertia_readback_kg_m2=inertia.tolist(),inertia_principal_values=eigen.tolist(),inertia_provenance='PhysX calculated from collision proxy and assumed total mass; uniform-density proxy, not real internal mass distribution',mobility={'force_n':[15.,0,0],'duration_s':.2,'horizontal_displacement_m':displacement,'minimum_m':.002},source_obj_sha256=spec['mesh_sha256'],color_authorship='TripoSR image-derived sRGB vertex colors converted to linear; explicit diffuse PreviewSurface roughness .85 metallic0 assumed',geometry_proxy='PhysX convexDecomposition cooking; local concavity/contact fidelity unverified')
  stage.GetRootLayer().Export(str(out/'scene_final.usda'))
 except Exception as e:result['error']=repr(e);raise
 finally:
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  if view is not None:
   from parcel_forge.carton_lifecycle import release_view
   release_view(view)
  runtime.close()
 return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
