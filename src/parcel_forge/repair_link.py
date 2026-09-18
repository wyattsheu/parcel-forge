"""Verify frozen source -> proposal -> candidate -> measured validation hashes."""
import json
from pathlib import Path
from .repair_guard import apply_proposal
from .upstream_bridge import FILES,digest,evaluate


def verify_link(proposal_dir, validation_dir):
    proposal_dir=Path(proposal_dir);validation_dir=Path(validation_dir)
    result=json.loads((proposal_dir/'proposal_result.json').read_text())
    if result['status']!='accepted_for_validation':raise ValueError('proposal was not accepted')
    receipt=json.loads((proposal_dir/'attempt_receipt.json').read_text())
    if receipt!={key:result[key] for key in ('source_run','source_spec_sha256','attempt')}:
        raise ValueError('controller attempt receipt mismatch')
    inputs=proposal_dir/'inputs'
    evaluate(inputs,result['source_input_sha256'])
    for name,key in [('source.json','source_spec_sha256'),('proposal.json','proposal_sha256'),('candidate.json','candidate_sha256')]:
        if digest(proposal_dir/name)!=result[key]:raise ValueError(f'repair hash mismatch: {name}')
    expected=apply_proposal(json.loads((proposal_dir/'source.json').read_text()),
        json.loads((proposal_dir/'proposal.json').read_text()),source_run=result['source_run'],
        source_spec_sha256=result['source_spec_sha256'],attempt=result['attempt'])
    if expected!=json.loads((proposal_dir/'candidate.json').read_text()):raise ValueError('candidate differs from allowed patch')
    if digest(validation_dir/'request.json')!=result['candidate_sha256']:
        raise ValueError('validation run used a different candidate')
    if digest(validation_dir/'profile.json')!=result['source_input_sha256']['profile.json']:
        raise ValueError('validation run changed source profile')
    measured=evaluate(validation_dir,{n:digest(validation_dir/n) for n in FILES})
    return {'status':'hash_chain_verified','source_run':result['source_run'],
            'proposal_run':proposal_dir.name,'validation_run':validation_dir.name,
            'candidate_sha256':result['candidate_sha256'],'task_gate':measured,
            'note':'Content linkage only; does not establish temporal execution order or a new physics run.'}


def main(argv):
    import argparse
    from .evidence import REPO_ROOT,make_run_dir,write_json
    parser=argparse.ArgumentParser();parser.add_argument('--proposal-run',required=True);parser.add_argument('--validation-run',required=True)
    args=parser.parse_args(argv);root=Path(REPO_ROOT)/'runs';out=Path(make_run_dir('s5d_repair_link'));code=1
    try:
        dirs=[(root/v).resolve() for v in (args.proposal_run,args.validation_run)]
        if any(d.parent!=root.resolve() for d in dirs):raise ValueError('run paths must be direct local runs')
        result=verify_link(*dirs);code=0 if result['task_gate']['task_acceptance']=='pass' else 1
    except Exception as exc:result={'status':'rejected','reason':str(exc)}
    result['exit_code']=code;write_json(str(out/'link_result.json'),result)
    print('run:',out);print(json.dumps(result,indent=2));return code
