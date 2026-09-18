"""USD-only topology/units and official rules; no Kit or GPU simulation."""
import argparse,json,math
from pathlib import Path
from pxr import Usd,UsdGeom,UsdPhysics
from parcel_forge.validation.official_usd import run_official_validation

def topology(stage,config):
    names=['MajorYN','MajorYP','MinorXP','MinorXN'];joints=[p for p in stage.Traverse() if p.IsA(UsdPhysics.RevoluteJoint)]
    plates=[p for p in stage.Traverse() if p.IsA(UsdGeom.Cube)]
    checks={'four_hinges':len(joints)==4,'nine_plates':len(plates)==9,'all_plates_collidable':all(p.HasAPI(UsdPhysics.CollisionAPI) and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()!=False for p in plates),'meters_z_up':UsdGeom.GetStageMetersPerUnit(stage)==1 and UsdGeom.GetStageUpAxis(stage)=='Z'}
    # Limits come from the config: the asset folds right out to 270 now, and this check
    # still hard-coded the old 100 degree stop.
    lower=config.get('crease_lower_limit_deg',-5);upper=config.get('crease_upper_limit_deg',100)
    checks['joint_limits']=all(UsdPhysics.RevoluteJoint(p).GetLowerLimitAttr().Get()==lower and UsdPhysics.RevoluteJoint(p).GetUpperLimitAttr().Get()==upper for p in joints)
    checks['gain_units']=all(math.isclose(UsdPhysics.DriveAPI(p,'angular').GetStiffnessAttr().Get(),config['stiffness_nm_rad']*math.pi/180,rel_tol=1e-6) for p in joints)
    checks['link_connections']=all(UsdPhysics.RevoluteJoint(stage.GetPrimAtPath('/World/Carton/Hinge'+n)).GetBody1Rel().GetTargets()==[stage.GetPrimAtPath('/World/Carton/'+n).GetPath()] for n in names if stage.GetPrimAtPath('/World/Carton/Hinge'+n)) and len(joints)==4
    return checks

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();source=Path(a.source);out=Path(a.out)
    config=json.loads((source/'config.json').read_text());stage=Usd.Stage.Open(str(source/'asset.usda'));checks=topology(stage,config)
    negatives=[]
    for label in ['missing_hinge','collision_disabled']:
        copy=Usd.Stage.Open(str(source/'asset.usda')).Flatten();fixture=out/(label+'.usda');copy.Export(str(fixture));broken=Usd.Stage.Open(str(fixture))
        if label=='missing_hinge':broken.RemovePrim('/World/Carton/HingeMinorXP')
        else:UsdPhysics.CollisionAPI(broken.GetPrimAtPath('/World/Carton/MinorXP/Panel')).CreateCollisionEnabledAttr(False)
        broken.GetRootLayer().Save();bad=topology(broken,config);negatives.append({'fixture':fixture.name,'detected':not all(bad.values()),'checks':bad})
    official=run_official_validation(str(source/'asset.usda'))
    fixture=out/'invalid_default_prim.usda';stage.Flatten().Export(str(fixture));broken=Usd.Stage.Open(str(fixture));broken.SetDefaultPrim(broken.GetPrimAtPath('/World/Carton'));broken.GetRootLayer().Save()
    official_negative=run_official_validation(str(fixture));official_can_fail=official_negative['status']=='fail' and any(issue['rule']=='DefaultPrimChecker' for issue in official_negative.get('failures',[]))
    report={'status':'pass' if all(checks.values()) and all(n['detected'] for n in negatives) and official['status']=='pass' and official_can_fail else 'fail','custom_checks':checks,'negative_tests':negatives,'official':official,'official_negative':{'fixture':fixture.name,'detected':official_can_fail,'failures':official_negative.get('failures',[])},'physics_execution':'not_tested','render':'not_tested','material_calibration':'not_tested','scope':'generic USD rule coverage plus carton topology; not cardboard mechanics, robot usability, SimReady certification or physics resume'}
    (out/'usd_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
