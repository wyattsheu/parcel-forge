"""Thin adapter to pinned official prepare/check/finalize plus the ITRI gate."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from .evidence import REPO_ROOT,make_run_dir,write_json
from .upstream_bridge import FILES,digest,evaluate


def main(argv):
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    args=parser.parse_args(argv);root=Path(REPO_ROOT)
    out=Path(make_run_dir('s5d_focused_gate'))
    result={'status':'insufficient_evidence','errors':[],'model_execution':'not_tested',
            'physics_reexecution':'not_tested','render':'not_tested','webrtc_human_view':'not_tested'}
    code=4
    try:
        source=(root/'runs'/args.run).resolve()
        if source.parent!=(root/'runs').resolve():raise ValueError('source must be a local run')
        pinned=json.loads((root/'config/upstream_content_agents.json').read_text())
        upstream=root/'external/usd-content-agents'
        commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
        # Existing provenance fields are read from the pinned configuration.
        expected=pinned['commit']
        if commit!=expected:raise ValueError('upstream commit differs from pin')
        if subprocess.check_output(['git','-C',str(upstream),'status','--porcelain'],text=True).strip():
            raise ValueError('upstream source is dirty')
        inputs=out/'inputs';inputs.mkdir()
        for name in FILES:shutil.copyfile(source/name,inputs/name)
        hashes={name:digest(inputs/name) for name in FILES};write_json(str(out/'input_hashes.json'),hashes)
        itri=evaluate(inputs,hashes);result['itri']=itri
        cli=root/'.venvs/usd-content-agents/bin/content-workflow-cli'
        official=out/'official'
        commands=[('prepare',[str(cli),'validate','prepare','--usd',str(inputs/'asset.usda'),
            '--task','Check physics sanity only; task containment is independently recomputed from frozen CSV.',
            '--template','physics_sane','--output-dir',str(official),'--json']),
            ('check',[str(cli),'validate','check','--output-dir',str(official),'--template','physics_sane','--json']),
            ('finalize',[str(cli),'validate','finalize','--output-dir',str(official),'--json'])]
        for name,command in commands:
            with (out/(name+'.log')).open('w') as log:
                process=subprocess.run(command,cwd=upstream,stdout=log,stderr=subprocess.STDOUT,timeout=120)
            write_json(str(out/(name+'_command.json')),{'command':command,'exit_code':process.returncode})
            if process.returncode:raise RuntimeError(f'official {name} failed; see log')
        operation=json.loads((official/'operations/physics_sane/operation_result.json').read_text())
        if operation['nested_agent_launched']:raise ValueError('unexpected nested agent')
        verdict=json.loads((official/'validation_result.json').read_text())['verdict']
        if operation['template_result']['status']!='passed' and verdict=='pass':
            raise ValueError('official template/final verdict mismatch')
        result['official']={'commit':commit,'template':'physics_sane','verdict':verdict,
            'operation_result':'official/operations/physics_sane/operation_result.json',
            'focused_flow':'prepare/check/finalize','checkpoint_resume':'not_tested'}
        evaluate(inputs,hashes)
        accepted=verdict=='pass' and itri['task_acceptance']=='pass'
        result['status']='pass' if accepted else 'fail';code=0 if accepted else 1
    except Exception as exc:result['errors'].append(str(exc))
    result['exit_code']=code;write_json(str(out/'focused_result.json'),result)
    print('run:',out);print(json.dumps(result,indent=2));return code
