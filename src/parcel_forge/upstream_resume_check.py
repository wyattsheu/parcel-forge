"""Controlled official checkpoint recovery; no model or new physics."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def child(out, source, phase, template):
    from world_understanding.validation import ValidationRequest
    from content_agent_workflows.validation.workflow import (
        run_validation_workflow,ScaffoldValidationStepExecutor)
    request=ValidationRequest(inputs=(str(source),),task_description='Controlled checkpoint recovery qualification for '+template+'.',requested_templates=(template,),render={'backend':'ovrtx'})
    if phase=='identity_mismatch':
        request=ValidationRequest.model_validate_json((out/'validation_request.json').read_text())
        request=request.model_copy(update={'task_description':request.task_description+' changed request'})
        try:run_validation_workflow(request,output_dir=out,config_base_dir=out.parent,resume=True)
        except Exception as exc:
            print(json.dumps({'exception':type(exc).__name__,'reason':str(exc)}));return 2
        return 1
    delegate=ScaffoldValidationStepExecutor(out.parent)
    class InterruptOnce:
        @property
        def template_versions(self):return delegate.template_versions
        def plan(self,*args,**kwargs):return delegate.plan(*args,**kwargs)
        def run(self,template_name,context):
            # Interrupt only this trusted process after official RUNNING claim.
            raise KeyboardInterrupt('parcel-forge controlled interruption before adapter execution')
    try:run_validation_workflow(request,output_dir=out,config_base_dir=out.parent,executor=InterruptOnce())
    except KeyboardInterrupt as exc:
        print(json.dumps({'status':'controlled_interruption','reason':str(exc)}));return 130
    return 1


def main(argv):
    parser=argparse.ArgumentParser();parser.add_argument('--run');parser.add_argument('--template',choices=['physics_sane','render_valid'],default='physics_sane');parser.add_argument('--child',choices=['interrupt','identity_mismatch']);parser.add_argument('--out');parser.add_argument('--source')
    args=parser.parse_args(argv)
    if args.child:return child(Path(args.out),Path(args.source),args.child,args.template)
    if not args.run:parser.error('--run is required')
    from .evidence import REPO_ROOT,make_run_dir,write_json
    from .upstream_bridge import FILES,digest,evaluate
    root=Path(REPO_ROOT);out=Path(make_run_dir('s5d_resume_check'));result={'status':'insufficient_evidence','errors':[],'model_execution':'not_tested','render':'not_tested','physics_reexecution':'not_tested','template':args.template};code=4
    try:
        source=(root/'runs'/args.run).resolve()
        if source.parent!=(root/'runs').resolve():raise ValueError('source must be a local run')
        inputs=out/'inputs';inputs.mkdir()
        for name in FILES:(inputs/name).write_bytes((source/name).read_bytes())
        hashes={name:digest(inputs/name) for name in FILES};write_json(str(out/'input_hashes.json'),hashes);evaluate(inputs,hashes)
        python=root/'.venvs/usd-content-agents/bin/python';cli=root/'.venvs/usd-content-agents/bin/content-workflow-cli';official=out/'official';official.mkdir()
        def execute(name,command):
            with (out/(name+'.log')).open('w') as log:p=subprocess.run(command,env=child_env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
            write_json(str(out/(name+'_command.json')),{'command':command,'exit_code':p.returncode});return p.returncode
        common=[str(python),'-B','-m','parcel_forge.upstream_resume_check','--out',str(official),'--source',str(inputs/'asset.usda'),'--template',args.template]
        # The isolated interpreter needs repo modules, without altering shared env.
        import os
        if (root/'.venvs/ovrtx-resume-probe-not-provisioned').exists():
            raise ValueError('probe renderer path unexpectedly exists; refuse a render launch')
        child_env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',WU_OVRTX_AUTO_PROVISION='0',WU_OVRTX_VENV_DIR=str(root/'.venvs/ovrtx-resume-probe-not-provisioned'))
        interrupted_exit=execute('interrupt',common+['--child','interrupt'])
        if args.template=='physics_sane':
            if 'Wave 2 supports only render_valid and look_right' not in (out/'interrupt.log').read_text():
                raise ValueError('unexpected physics_sane failure')
            result.update(status='not_supported',exit_code=4,unsupported_api='run_validation_workflow/resume',reason='Pinned Wave 2 resume accepts visual templates only, not physics_sane')
            write_json(str(out/'resume_result.json'),dict(result,exit_code=4))
            print('run:',out);print(json.dumps(result,indent=2));return 4
        if interrupted_exit!=130:raise ValueError('controlled interrupt did not exit 130')
        checkpoint=official/'validation_checkpoint.json';interrupted=json.loads(checkpoint.read_text());write_json(str(out/'checkpoint_interrupted.json'),interrupted)
        if not any(r['state']=='running' for r in interrupted['records']):raise ValueError('no running checkpoint claim after interruption')
        if (official/'validation_result.json').exists():raise ValueError('interrupted run published terminal result')
        mismatch_code=execute('identity_mismatch',common+['--child','identity_mismatch'])
        mismatch=(out/'identity_mismatch.log').read_text()
        if mismatch_code!=2 or 'ValidationWorkflowIdentityMismatch' not in mismatch:raise ValueError('request identity mismatch was not rejected')
        resume=[str(cli),'validate','resume','--output-dir',str(official),'--json']
        refused=execute('resume_without_recovery',resume)
        if refused==0:raise ValueError('resume unexpectedly accepted unrecovered claim')
        result['unrecovered_claim_exit']=refused
        # interrupt subprocess was awaited and has exited; only our claim is recovered.
        recovered_exit=execute('resume_recovered',resume+['--recover-orphaned-claims'])
        if recovered_exit!=1:raise ValueError('expected validation fail exit 1 after completed recovery')
        result['recovered_claim_exit']=recovered_exit
        final=json.loads((official/'validation_result.json').read_text())
        if 'render.renderer_unavailable' not in [i['code'] for i in final['issues']]:
            raise ValueError('expected unavailable-renderer finding missing')
        completed=json.loads(checkpoint.read_text());write_json(str(out/'checkpoint_completed.json'),completed)
        if final['verdict']!='fail' or not all(r['state']=='completed' and r['attempts']==2 for r in completed['records']):raise ValueError('recovered result/checkpoint not complete')
        evaluate(inputs,hashes)
        result.update(status='pass',interruption_exit=130,identity_mismatch_exit=2,final_verdict=final['verdict'],attempts=[r['attempts'] for r in completed['records']],scope='official render_valid state recovery with intentionally unavailable OVRTX; final asset validation remains fail; no renderer/model/physics recovery claim')
        code=0
    except Exception as exc:result['errors'].append(str(exc))
    result['exit_code']=code;write_json(str(out/'resume_result.json'),result);print('run:',out);print(json.dumps(result,indent=2));return code

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
