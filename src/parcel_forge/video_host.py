"""Recorded-rollout export/render/encode adapter, not a simulation workflow."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
from .evidence import REPO_ROOT,make_run_dir,write_json
from .upstream_bridge import FILES,digest,evaluate
from . import envprobe
from .runtime.launcher import IsaacLauncher


def main(argv):
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    args=parser.parse_args(argv);root=Path(REPO_ROOT)
    source=(root/'runs'/args.run).resolve();out=Path(make_run_dir('s5c_recorded_video'))
    result={'source_run':args.run,'status':'insufficient_evidence','errors':[],
            'video':None,'webrtc_human_view':'not_tested',
            'adapter_sha256':{name:digest(root/'src/parcel_forge'/name) for name in
                ('recording_export.py','recording_render.py','video_host.py')}}
    code=4
    try:
        if source.parent!=(root/'runs').resolve():raise ValueError('source must be a local run')
        frozen=out/'inputs';frozen.mkdir()
        for name in FILES:shutil.copyfile(source/name,frozen/name)
        hashes={name:digest(frozen/name) for name in FILES}
        write_json(str(out/'input_hashes.json'),hashes)
        result['task']=evaluate(frozen,hashes)
        cmd=[str(root/'.venvs/usd-content-agents/bin/python'),
             str(root/'src/parcel_forge/recording_export.py'),'--input',str(frozen),'--out',str(out)]
        with (out/'export.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        write_json(str(out/'export_command.json'),{'command':cmd,'exit_code':p.returncode})
        if p.returncode:raise RuntimeError('recording export failed; see export.log')
        result['recording']=json.loads((out/'recording_validation.json').read_text())
        recording_hash=digest(out/'recording.usda')
        # Prefer canonical upstream render, explicitly with provisioning disabled.
        env=dict(os.environ,WU_OVRTX_AUTO_PROVISION='0',
                 WU_OVRTX_VENV_DIR=str(root/'.venvs/ovrtx-not-provisioned'))
        probe_script="from world_understanding.functions.graphics.render_time_sampled_usd import render_time_sampled_usd; import sys; render_time_sampled_usd(sys.argv[1],sys.argv[2],renderer='ovrtx',frames='1',fps=30,cameras=['/World/RecordingCamera'],max_duration_seconds=4)"
        cmd=[str(root/'.venvs/usd-content-agents/bin/python'),'-c',probe_script,
             str(out/'recording.usda'),str(out/'upstream_render_probe')]
        with (out/'upstream_render_probe.log').open('w') as log:
            p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        write_json(str(out/'upstream_render_probe_command.json'),{'command':cmd,'exit_code':p.returncode})
        result['upstream_render_probe_exit']=p.returncode
        # Explicitly selected installed-Isaac adapter: no mock or generated imagery.
        gpu=envprobe.gpu_info();write_json(str(out/'gpu_before_render.json'),gpu)
        if gpu['status']!='ok' or not gpu['gpus'] or gpu['gpus'][0]['memory_free_mib']<8000:
            write_json(str(out/'blocked.json'),{'reason':'GPU 0 free VRAM unavailable or below 8000 MiB'})
            raise RuntimeError('render blocked: insufficient known free VRAM')
        launch=IsaacLauncher().run(str(root/'src/parcel_forge/recording_render.py'),
            ['--recording',str(out/'recording.usda'),'--out',str(out)],
            log_path=str(out/'render.log'),timeout=1800)
        write_json(str(out/'render_launch.json'),launch)
        if launch['external_exit_code']!=0:raise RuntimeError('recorded renderer process failed')
        render=json.loads((out/'render_result.json').read_text());result['render']={k:v for k,v in render.items() if k!='frames'}
        if render['status']!='pass':raise RuntimeError('recorded frames failed blank/motion checks')
        video=out/'test_recording.mp4'
        (out/'video_caption.txt').write_text(result['task']['case_id']+' | source '+args.run+' | measured recording, 0.25x')
        cmd=['ffmpeg','-nostdin','-v','error','-framerate','30','-i',str(out/'frames/frame_%05d.png'),
             '-vf',f'drawtext=textfile={out}/video_caption.txt:fontcolor=white:fontsize=16:box=1:boxcolor=black@0.7:x=12:y=12','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
        with (out/'encode.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        write_json(str(out/'encode_command.json'),{'command':cmd,'exit_code':p.returncode})
        if p.returncode:raise RuntimeError('MP4 encoding failed')
        cmd=['ffprobe','-v','error','-count_frames','-select_streams','v:0',
             '-show_entries','stream=codec_name,width,height,nb_read_frames,duration','-of','json',str(video)]
        p=subprocess.run(cmd,capture_output=True,text=True);(out/'ffprobe.json').write_text(p.stdout)
        stream=json.loads(p.stdout)['streams'][0]
        if p.returncode or int(stream['nb_read_frames'])!=render['frame_count']:raise RuntimeError('video verification mismatch')
        (out/'ffmpeg_version.txt').write_text(subprocess.check_output(['ffmpeg','-version'],text=True))
        evaluate(frozen,hashes)
        if digest(out/'recording.usda')!=recording_hash:raise RuntimeError('recording changed during rendering')
        result.update(status='pass',video='test_recording.mp4',video_sha256=digest(video),
                      recording_sha256=digest(out/'recording.usda'),ffprobe=stream,
                      frame_hashes={f.name:digest(f) for f in sorted((out/'frames').glob('*.png'))})
        code=0
    except Exception as exc:result['errors'].append(str(exc))
    result['exit_code']=code;write_json(str(out/'video_result.json'),result)
    (out/'summary.md').write_text('# Recorded test video\n\n'+json.dumps(result,indent=2)+'\n')
    print('run:',out);print(json.dumps({k:v for k,v in result.items() if k!='frame_hashes'},indent=2))
    return code
