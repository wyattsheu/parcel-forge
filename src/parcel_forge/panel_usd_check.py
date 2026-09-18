"""New segmented topology profile; original rigid carton validator unchanged."""
import argparse,json,math
from pathlib import Path
from pxr import Usd,UsdGeom,UsdPhysics
from parcel_forge.validation.official_usd import run_official_validation
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();source=Path(a.source);out=Path(a.out)
stage=Usd.Stage.Open(str(source/'asset.usda'));c=json.loads((source/'config.json').read_text());joints=[x for x in stage.Traverse() if x.IsA(UsdPhysics.RevoluteJoint)];plates=[x for x in stage.Traverse() if x.IsA(UsdGeom.Cube)]
checks={'16_joints':len(joints)==16,'21_collidable_plates':len(plates)==21 and all(x.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(x).GetCollisionEnabledAttr().Get()!=False for x in plates),'bend_units':all(math.isclose(UsdPhysics.DriveAPI(stage.GetPrimAtPath('/World/Carton/'+n),'angular').GetStiffnessAttr().Get(),v['stiffness_nm_rad']*math.pi/180,rel_tol=1e-6) for n,v in c['panel_bend_joints'].items())}
official=run_official_validation(str(source/'asset.usda'));result={'status':'pass' if all(checks.values()) and official['status']=='pass' else 'fail','checks':checks,'official':official,'physics':'not_tested','human_view':'not_tested'}
(out/'usd_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status']);raise SystemExit(0 if result['status']=='pass' else 1)
