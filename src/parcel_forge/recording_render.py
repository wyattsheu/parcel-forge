"""Render recorded USD in the installed Isaac Kit; timeline never plays physics."""
import argparse
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--recording',required=True)
parser.add_argument('--out',required=True)
args=parser.parse_args()
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.pngio import image_stats,write_rgb_png
runtime=IsaacSimRuntime(headless=True,enable_cameras=True)
result={'status':'error','renderer':'isaac_sim_kit_rtx','physics_execution':'disabled',
        'width':960,'height':540,'fps':30,'playback_speed':0.25,'frames':[]}
out=Path(args.out);(out/'frames').mkdir(parents=True,exist_ok=True)
exit_code=4
try:
    runtime.start()
    import omni.usd
    import omni.timeline
    import omni.replicator.core as rep
    from pxr import Usd,UsdPhysics
    omni.usd.get_context().open_stage(args.recording)
    runtime.stage=omni.usd.get_context().get_stage()
    timeline=omni.timeline.get_timeline_interface();timeline.stop()
    assert not list(p for p in runtime.stage.Traverse() if p.IsA(UsdPhysics.Scene))
    assert all(not UsdPhysics.RigidBodyAPI(p).GetRigidBodyEnabledAttr().Get()
        for p in runtime.stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI))
    start=runtime.stage.GetStartTimeCode();end=runtime.stage.GetEndTimeCode()
    tps=runtime.stage.GetTimeCodesPerSecond()
    product=rep.create.render_product('/World/RecordingCamera',(960,540))
    annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
    count=int((end-start)/tps/result['playback_speed']*result['fps'])+1
    previous=None;motion=0;blank=0
    for index in range(count):
        tc=min(end,start+index*tps*result['playback_speed']/result['fps'])
        timeline.set_current_time(tc/tps)
        rep.orchestrator.step(rt_subframes=8 if index==0 else 2,
                              delta_time=0.0,pause_timeline=True,wait_for_render=True)
        if abs(timeline.get_current_time()-tc/tps)>1e-7:
            raise RuntimeError('render timeline drifted from recorded timestamp')
        data=annotator.get_data()
        if data is None or getattr(data,'size',0)==0:raise RuntimeError('empty recorded frame')
        pixels=data[:,:,:3].tobytes();h,w=data.shape[:2]
        stats=image_stats(w,h,pixels,3);blank+=int(stats['looks_blank'])
        if previous is not None:motion=max(motion,sum(a!=b for a,b in zip(previous,pixels)))
        previous=pixels
        filename=f'frames/frame_{index:05d}.png'
        write_rgb_png(str(out/filename),w,h,pixels,3)
        result['frames'].append({'path':filename,'source_time_s':tc/tps,'stats':stats})
        if index%30==0:
            (out/'render_checkpoint.json').write_text(json.dumps(result,indent=2))
            print(f'recorded frames {index+1}/{count}',flush=True)
    annotator.detach();product.destroy()
    result.update(status='pass' if blank==0 and motion>100 else 'fail',
                  blank_frames=blank,max_changed_rgb_bytes=motion,frame_count=count)
    exit_code=0 if result['status']=='pass' else 1
except Exception as exc:
    result['error']=str(exc)
finally:
    (out/'render_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='frames'}),flush=True)
    runtime.close()
sys.exit(exit_code)
