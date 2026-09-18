"""Recorded measured world poses for human playback, separate from physics asset."""
import csv,json
from pxr import Usd,UsdGeom,UsdPhysics,Gf

def export_recording(out):
    rows=list(csv.DictReader((out/'link_poses.csv').open()))
    stage=Usd.Stage.Open(str(out/'asset.usda'))
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdPhysics.Joint) or prim.IsA(UsdPhysics.Scene):stage.RemovePrim(prim.GetPath())
        elif prim.HasAPI(UsdPhysics.RigidBodyAPI):UsdPhysics.RigidBodyAPI(prim).CreateRigidBodyEnabledAttr(False)
    ops={}
    for row in rows:
        name=row['link']
        if name not in ops:
            xf=UsdGeom.Xformable(stage.GetPrimAtPath('/World/Carton/'+name));xf.ClearXformOpOrder()
            ops[name]=(xf.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble),xf.AddOrientOp(UsdGeom.XformOp.PrecisionDouble))
        tc=float(row['time_s'])*30
        ops[name][0].Set(Gf.Vec3d(*[float(row[k]) for k in ['px','py','pz']]),tc)
        ops[name][1].Set(Gf.Quatd(float(row['qw']),Gf.Vec3d(*[float(row[k]) for k in ['qx','qy','qz']])),tc)
    stage.SetTimeCodesPerSecond(30);stage.SetFramesPerSecond(30);stage.SetStartTimeCode(0);stage.SetEndTimeCode(float(rows[-1]['time_s'])*30)
    stage.Export(str(out/'recording.usda'))
    reopened=Usd.Stage.Open(str(out/'recording.usda'));error=0.0
    for row in rows:
        prim=reopened.GetPrimAtPath('/World/Carton/'+row['link']);tc=float(row['time_s'])*30
        pos=prim.GetAttribute('xformOp:translate').Get(tc);q=prim.GetAttribute('xformOp:orient').Get(tc)
        values=[*pos,q.GetReal(),*q.GetImaginary()]
        error=max(error,max(abs(v-float(row[k])) for v,k in zip(values,['px','py','pz','qw','qx','qy','qz'])))
    report={'status':'pass' if error<=1e-12 else 'fail','samples':len(rows),'max_component_error':error,'physics_disabled_only_in_recording':True,'scope':'measured 30 Hz playback; not physics validation or live plastic controller; last interval after last recorded pose omitted'}
    (out/'recording_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
