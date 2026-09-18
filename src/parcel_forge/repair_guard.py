"""Pure spec-proposal gate; no model runner, checkpoint or validator replacement."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from .schema import validate_case
from .evidence import REPO_ROOT,make_run_dir,sha256_file,write_json
from .upstream_bridge import FILES,digest,evaluate
import fcntl
import re


def apply_proposal(source, proposal, *, source_run, source_spec_sha256, attempt):
    """Only remove a known injected geometry fault; all task fields stay fixed."""
    if validate_case(source):
        raise ValueError('source case is invalid')
    if source['intended_task'] != 'place_object_inside':
        raise ValueError('unsupported task')
    if not isinstance(proposal,dict) or set(proposal)!={'schema','source_run','source_spec_sha256','attempt','changes'}:
        raise ValueError('proposal must match the v2 envelope')
    if proposal['schema']!='parcel_forge.repair_proposal/2':
        raise ValueError('unknown proposal schema')
    if not isinstance(proposal['source_run'],str) or not re.fullmatch(r'[A-Za-z0-9_-]+',proposal['source_run']):
        raise ValueError('invalid source run id')
    if not isinstance(proposal['source_spec_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',proposal['source_spec_sha256']):
        raise ValueError('invalid source spec hash')
    if type(proposal['attempt']) is not int or not 1<=proposal['attempt']<=3:
        raise ValueError('attempt must be an integer from 1 to 3')
    if (proposal['source_run'],proposal['source_spec_sha256'],proposal['attempt'])!=(source_run,source_spec_sha256,attempt):
        raise ValueError('source binding or attempt mismatch')
    changes=proposal['changes']
    if not isinstance(changes,list) or len(changes)!=1:
        raise ValueError('exactly one fault removal is allowed')
    change=changes[0]
    if not isinstance(change,dict) or set(change)!={'path','from','to'}:
        raise ValueError('change must contain only path/from/to')
    if change['path']!='/geometry/fault' or change['to']!='none':
        raise ValueError('change outside repair allowlist')
    if source['geometry']['fault'] not in ('sealed_lid','missing_bottom'):
        raise ValueError('source fault is not a supported repair')
    if change['from']!=source['geometry']['fault']:
        raise ValueError('proposal stale: source fault mismatch')
    candidate=deepcopy(source);candidate['geometry']['fault']='none'
    if validate_case(candidate):raise ValueError('candidate case is invalid')
    return candidate



def allowed_file(path, root, allowed_roots):
    path=Path(path).absolute()
    if any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('symlink inputs are not allowed')
    resolved=path.resolve()
    if not any(resolved.is_relative_to(root/r) for r in allowed_roots):
        raise ValueError('input path outside allowlist')
    if not resolved.is_file():raise ValueError('input must be a regular file')
    return resolved


def submit(source_run, proposal_path, *, root=None):
    root=Path(root or REPO_ROOT).resolve();runs=root/'runs'
    # make_run_dir is used on the real repo; isolated tests use a unique directory.
    if root==Path(REPO_ROOT).resolve():out=Path(make_run_dir('s5d_repair_proposal'))
    else:
        import tempfile
        out=Path(tempfile.mkdtemp(prefix='fixture_s5d_repair_proposal_',dir=runs))
    result={'status':'rejected','physics_execution':'not_tested',
            'official_agent_execution':'not_tested','video':'not_requested'}
    code=1
    try:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',source_run):raise ValueError('invalid source run id')
        source=runs/source_run
        if source.is_symlink():raise ValueError('symlink source run rejected')
        proposal_path=allowed_file(proposal_path,root,['contracts/repair_proposals','runs'])
        inputs=out/'inputs';inputs.mkdir()
        for name in FILES:
            original=allowed_file(source/name,root,['runs'])
            (inputs/name).write_bytes(original.read_bytes())
        hashes={n:digest(inputs/n) for n in FILES}
        evaluate(inputs,hashes)
        source_hash=hashes['request.json']
        result.update(source_run=source_run,source_spec_sha256=source_hash,source_input_sha256=hashes)
        (out/'source.json').write_bytes((inputs/'request.json').read_bytes())
        # Controller-owned append-only receipts count even rejected attempts.
        with (runs/'.repair-budget.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            receipts=[]
            for receipt in runs.glob('*s5d_repair_proposal*/attempt_receipt.json'):
                item=json.loads(receipt.read_text())
                if item['source_run']==source_run:
                    if item['source_spec_sha256']!=source_hash:raise ValueError('source changed since previous attempt')
                    receipts.append(item)
            attempt=len(receipts)+1
            if attempt>3:raise ValueError('budget_exhausted: maximum three submissions per source run')
            write_json(str(out/'attempt_receipt.json'),{'source_run':source_run,'source_spec_sha256':source_hash,'attempt':attempt})
        result['attempt']=attempt
        (out/'proposal.json').write_bytes(proposal_path.read_bytes())
        proposal_hash=digest(out/'proposal.json')
        candidate=apply_proposal(json.loads((out/'source.json').read_text()),
            json.loads((out/'proposal.json').read_text()),source_run=source_run,
            source_spec_sha256=source_hash,attempt=attempt)
        write_json(str(out/'candidate.json'),candidate)
        result.update(status='accepted_for_validation',proposal_sha256=proposal_hash,
            candidate_sha256=digest(out/'candidate.json'),note='original expected_outcome preserved; acceptance requires new measured task gate')
        code=0
    except Exception as exc:result['reason']=str(exc)
    result['exit_code']=code;write_json(str(out/'proposal_result.json'),result)
    return code,out,result


def main(argv):
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-run',required=True)
    parser.add_argument('--proposal',required=True)
    args=parser.parse_args(argv)
    code,out,result=submit(args.source_run,args.proposal)
    print('run:',out);print(json.dumps(result,indent=2));return code
