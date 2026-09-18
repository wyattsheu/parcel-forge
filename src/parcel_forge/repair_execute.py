"""Trusted bounded repair validation; reuses generators and official validators."""
import argparse
import contextlib
import json
from pathlib import Path
import re
import subprocess
from .evidence import REPO_ROOT,make_run_dir,write_json
from .repair_guard import allowed_file,apply_proposal
from .repair_link import verify_link
from .upstream_bridge import FILES,digest,evaluate


def check_accepted(directory):
    directory=Path(directory)
    result=json.loads((directory/'proposal_result.json').read_text())
    if result['status']!='accepted_for_validation':raise ValueError('proposal not accepted')
    receipt=json.loads((directory/'attempt_receipt.json').read_text())
    context={k:result[k] for k in ('source_run','source_spec_sha256','attempt')}
    if receipt!=context:raise ValueError('receipt mismatch')
    evaluate(directory/'inputs',result['source_input_sha256'])
    for file,key in [('source.json','source_spec_sha256'),('proposal.json','proposal_sha256'),('candidate.json','candidate_sha256')]:
        if digest(directory/file)!=result[key]:raise ValueError('proposal content changed: '+file)
    source=json.loads((directory/'source.json').read_text())
    if digest(directory/'inputs/request.json')!=result['source_spec_sha256']:raise ValueError('source snapshot mismatch')
    candidate=apply_proposal(source,json.loads((directory/'proposal.json').read_text()),**context)
    if candidate!=json.loads((directory/'candidate.json').read_text()):raise ValueError('candidate patch mismatch')
    return result


def available_gpu(device):
    proc=subprocess.run(['nvidia-smi','--query-gpu=index,memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
    if proc.returncode:raise ValueError('GPU inventory unavailable')
    inventory={int(a):int(b) for a,b in (line.split(',') for line in proc.stdout.strip().splitlines())}
    return inventory,inventory.get(device,0)>=8000


def main(argv):
    p=argparse.ArgumentParser();p.add_argument('--proposal-run',required=True);p.add_argument('--device',type=int,default=0);p.add_argument('--timeout',type=int,default=1800)
    args=p.parse_args(argv);root=Path(REPO_ROOT).resolve();out=Path(make_run_dir('s5d_repair_execution'))
    result={'status':'failed','model_execution':'not_tested','external_geometry_generation':'not_tested','physics_execution':'not_tested','webrtc_human_view':'not_tested','video':'not_requested','exit_code':1}
    try:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',args.proposal_run):raise ValueError('invalid proposal run id')
        original=root/'runs'/args.proposal_run;frozen=out/'proposal';frozen.mkdir()
        files=['proposal_result.json','attempt_receipt.json','source.json','proposal.json','candidate.json',*['inputs/'+n for n in FILES]]
        for name in files:
            source=allowed_file(original/name,root,['runs']);target=frozen/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        accepted=check_accepted(frozen)
        write_json(str(out/'01_proposal_checked.json'),{'status':'pass','proposal_run':args.proposal_run,'candidate_sha256':accepted['candidate_sha256']})
        inventory,ready=available_gpu(args.device);write_json(str(out/'02_gpu_inventory.json'),{'free_mib':inventory,'selected_device':args.device})
        if not ready:
            write_json(str(out/'blocked.json'),{'reason':'Selected GPU free VRAM below 8000 MiB','device':args.device});result['status']='blocked';result['exit_code']=4
            raise ValueError('GPU resources insufficient; no process stopped')
        from .box_host import run_case
        print('stage: physics',flush=True)
        with (out/'physics.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            code,validation,_=run_case(str(frozen/'candidate.json'),str(frozen/'inputs/profile.json'),str(args.device),args.timeout)
        validation=Path(validation)
        write_json(str(out/'03_physics_executed.json'),{'run':validation.name,'exit_code':code,'case':str(frozen/'candidate.json'),'profile':str(frozen/'inputs/profile.json')})
        result['validation_run']=validation.name
        # Do not treat fault fixture exit 2 as success without measured task acceptance.
        link=verify_link(frozen,validation);link['proposal_run']=args.proposal_run
        write_json(str(out/'04_link_checked.json'),link)
        if link['task_gate']['task_acceptance']!='pass':raise ValueError('measured task failed')
        result['physics_execution']='pass';result['asset_usd']=str(validation/'asset.usda');result['task_acceptance']='pass';result['regression_expectation']=link['task_gate']['regression_expectation']
        print('stage: official focused validation',flush=True)
        cmd=[str(root/'scripts/pf'),'upstream-focused-check','--run',validation.name]
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=420,cwd=root)
        (out/'official.log').write_text(proc.stdout+proc.stderr)
        match=re.search(r'^run: (.+)$',proc.stdout,re.MULTILINE)
        if not match:raise ValueError('official evidence run unavailable')
        official_dir=Path(match.group(1)).resolve()
        if official_dir.parent!=root/'runs':raise ValueError('official evidence outside local runs')
        official=json.loads((official_dir/'focused_result.json').read_text())
        write_json(str(out/'05_official_checked.json'),{'command':cmd,'exit_code':proc.returncode,'run':official_dir.name,'result':official})
        if proc.returncode or official['status']!='pass':raise ValueError('official focused gate failed')
        check_accepted(frozen);verify_link(frozen,validation)
        result.update(status='pass',exit_code=0,proposal_run=args.proposal_run,official_run=official_dir.name,note='New local generator USD and PhysX execution. Not external AI geometry generation.')
    except Exception as exc:result['reason']=str(exc)
    write_json(str(out/'execution_result.json'),result)
    print('run:',out);print(json.dumps(result,indent=2));return result['exit_code']
