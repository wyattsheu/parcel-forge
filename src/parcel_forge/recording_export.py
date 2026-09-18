"""Export measured S2 poses to animation USD; no simulation or invented motion."""
import argparse
import csv
import json
from pathlib import Path
from pxr import Gf, Usd, UsdGeom, UsdPhysics


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args(); source=Path(args.input); out=Path(args.out)
    rows=list(csv.DictReader((source/'trajectory.csv').open()))
    stage=Usd.Stage.Open(str(source/'asset.usda'))
    bodies=[p for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    if [str(p.GetPath()) for p in bodies] != ['/World/Probe']:
        raise ValueError('recording supports the single measured S2 probe only')
    for prim in bodies: UsdPhysics.RigidBodyAPI(prim).CreateRigidBodyEnabledAttr(False)
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdPhysics.Scene): stage.RemovePrim(prim.GetPath())
    probe=stage.GetPrimAtPath('/World/Probe')
    xform=UsdGeom.Xformable(probe);xform.ClearXformOpOrder()
    translate=xform.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble)
    orient=xform.AddOrientOp(UsdGeom.XformOp.PrecisionDouble)
    # Time codes preserve actual measured times, including the unrecorded warm-up offset.
    dt=json.loads((source/'profile.json').read_text())['simulation']['dt']
    tps=30.0
    stage.SetTimeCodesPerSecond(tps);stage.SetFramesPerSecond(30)
    stage.SetStartTimeCode(float(rows[0]['sim_time_s'])*tps)
    stage.SetEndTimeCode(float(rows[-1]['sim_time_s'])*tps)
    for row in rows:
        tc=float(row['sim_time_s'])*tps
        translate.Set(Gf.Vec3d(*[float(row[k]) for k in ('px_m','py_m','pz_m')]),tc)
        orient.Set(Gf.Quatd(float(row['qw']),Gf.Vec3d(*[float(row[k]) for k in ('qx','qy','qz')])),tc)
    camera=UsdGeom.Camera.Define(stage,'/World/RecordingCamera')
    camera.CreateFocalLengthAttr(35);camera.CreateClippingRangeAttr(Gf.Vec2f(0.01,100))
    eye=(0.65,-0.75,0.72);target=(0,0,0.23)
    UsdGeom.Xformable(camera).AddTransformOp().Set(Gf.Matrix4d().SetLookAt(
        Gf.Vec3d(*eye),Gf.Vec3d(*target),Gf.Vec3d(0,0,1)).GetInverse())
    stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    out.mkdir(parents=True,exist_ok=True)
    stage.Export(str(out/'recording.usda'))
    reopened=Usd.Stage.Open(str(out/'recording.usda'))
    pos=reopened.GetPrimAtPath('/World/Probe').GetAttribute('xformOp:translate')
    quat=reopened.GetPrimAtPath('/World/Probe').GetAttribute('xformOp:orient')
    pe=qe=0.0
    for row in rows:
        tc=float(row['sim_time_s'])*tps
        p=pos.Get(tc);q=quat.Get(tc);values=[q.GetReal(),*q.GetImaginary()]
        pe=max(pe,max(abs(p[i]-float(row[k])) for i,k in enumerate(('px_m','py_m','pz_m'))))
        qe=max(qe,max(abs(values[i]-float(row[k])) for i,k in enumerate(('qw','qx','qy','qz'))))
    assert pe<=1e-12 and qe<=1e-12
    report={'status':'pass','samples':len(rows),'position_max_error_m':pe,
        'quaternion_max_component_error':qe,'source_dt_s':dt,
        'source_seed':json.loads((source/'manifest.json').read_text())['seed'],'source_time_start_s':float(rows[0]['sim_time_s']),
        'source_time_end_s':float(rows[-1]['sim_time_s']),'time_codes_per_second':tps,
        'physics_disabled_in_recording':True,'camera_eye_m':eye,'camera_target_m':target,
        'limitations':'Only logged interval, no reconstruction before first CSV sample; single S2 probe.'}
    (out/'recording_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__': main()
