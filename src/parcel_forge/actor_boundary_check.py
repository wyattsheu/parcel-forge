"""Trusted adversarial probe; never runs a model or changes original assets."""
import argparse
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
from .actor_boundary import restrict_writes


def child(job):
    output=job/'outputs';protected=job/'protected.txt'
    try:boundary=restrict_writes(output)
    except Exception as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)}));return 4
    checks=[]
    def denied(name,operation):
        try:operation()
        except OSError as exc:
            checks.append({'name':name,'status':'pass' if exc.errno in (errno.EACCES,errno.EPERM,errno.EXDEV) else 'fail','errno':exc.errno})
        else:checks.append({'name':name,'status':'fail'})
    (output/'proposal.json').write_text('{"proposal":"allowed"}\n')
    checks.append({'name':'candidate_write','status':'pass'})
    # Existing file is only opened for writing, never written if unexpectedly allowed.
    def writable_open():
        fd=os.open(protected,os.O_WRONLY);os.close(fd)
    denied('protected_write_open',writable_open)
    denied('protected_create',lambda:(job/'forbidden.txt').write_text('unexpected'))
    denied('protected_delete',lambda:protected.unlink())
    # A separate disposable fixture tests truncate without risking repo originals.
    denied('protected_truncate',lambda:os.truncate(job/'truncate.txt',0))
    link=output/'escape';link.symlink_to(protected)
    denied('symlink_escape',lambda:link.write_text('unexpected'))
    denied('rename_escape',lambda:(output/'proposal.json').rename(job/'escaped.json'))
    fd=os.open(protected,os.O_RDONLY);os.close(fd)
    checks.append({'name':'protected_read','status':'pass'})
    # exec descendant must inherit the same restriction; attempts only controlled fixture.
    script='import os,sys\ntry: fd=os.open(sys.argv[1],os.O_WRONLY)\nexcept PermissionError: sys.exit(0)\nelse: os.close(fd);sys.exit(1)'
    process=subprocess.run([sys.executable,'-B','-c',script,str(protected)],capture_output=True,text=True)
    checks.append({'name':'descendant_write_denied','status':'pass' if process.returncode==0 else 'fail'})
    result={'status':'pass' if all(c['status']=='pass' for c in checks) else 'fail','boundary':boundary,'checks':checks,'model_execution':'not_tested'}
    print(json.dumps(result));return 0 if result['status']=='pass' else 1


def main(argv):
    from .evidence import make_run_dir,write_json
    parser=argparse.ArgumentParser();parser.add_argument('--child');args=parser.parse_args(argv)
    if args.child:return child(Path(args.child))
    job=Path(make_run_dir('s5d_actor_boundary'));(job/'outputs').mkdir()
    for name in ('protected.txt','truncate.txt'):(job/name).write_text('original\n')
    command=[sys.executable,'-B','-m','parcel_forge.actor_boundary_check','--child',str(job)]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=30)
    (job/'stdout.log').write_text(p.stdout);(job/'stderr.log').write_text(p.stderr)
    write_json(str(job/'command.json'),{'command':command,'exit_code':p.returncode})
    try:result=json.loads(p.stdout)
    except Exception:result={'status':'error','reason':'child result missing','exit_code':p.returncode}
    result['original_fixtures_unchanged']=all((job/n).exists() and (job/n).read_text()=='original\n' for n in ('protected.txt','truncate.txt'))
    if not result['original_fixtures_unchanged']:result['status']='fail'
    write_json(str(job/'boundary_result.json'),result)
    print('run:',job);print(json.dumps(result,indent=2));return 0 if p.returncode==0 and result['status']=='pass' else 4

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
