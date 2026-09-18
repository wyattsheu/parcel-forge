"""Small deterministic entry; normal operation reads results instead of source history."""
import argparse
import json
import re
import subprocess
from pathlib import Path

from parcel_forge.evidence import make_unique_run_dir, write_json, sha256_file
from parcel_forge.workflow.preflight import ROOT, evaluate
from parcel_forge.workflow.image_intake import prepare


def execute_stage(out, stages, name, script, source, field, expected='pass', extra=()):
    entry = {'stage': name, 'status': 'running', 'source_run': source.name}
    stages.append(entry)
    write_json(str(out / 'progress.json'), {'stages': stages})
    cmd = [str(ROOT / 'scripts' / script), '--run', str(source), *extra]
    write_json(str(out / (name + '_command.json')), {'command': cmd})
    try:
        with (out / (name + '.log')).open('w') as log:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=1800, cwd=ROOT)
        entry['exit_code'] = proc.returncode
        text = (out / (name + '.log')).read_text()
        matches = re.findall(r'^run:\s*(.+)$', text, re.M)
        if not matches:
            matches = re.findall(r'"run":\s*"([^"\n]+)"', text)
        if len(set(matches)) != 1:
            raise ValueError('missing or ambiguous stage run path')
        child = Path(matches[0]).resolve()
        if child.parent != ROOT / 'runs':
            raise ValueError('stage run outside project')
        measured = json.loads((child / 'result.json').read_text())
        entry.update(run=child.name, result_sha256=sha256_file(str(child / 'result.json')))
        if proc.returncode or measured.get(field) != expected:
            raise ValueError('stage failed; inspect saved stage log and child evidence')
        entry['status'] = 'pass'
        return child, measured
    except Exception:
        entry['status'] = 'fail'
        raise
    finally:
        write_json(str(out / 'progress.json'), {'stages': stages})


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    t = sub.add_parser('text')
    t.add_argument('--prompt-file', type=Path, required=True)
    t.add_argument('--bundle', type=Path, required=True)
    i = sub.add_parser('image')
    i.add_argument('--bundle', type=Path, required=True)
    i.add_argument('--image', type=Path, required=True)
    i.add_argument('--reference', required=True)
    i.add_argument('--license-note', required=True)
    i.add_argument('--execute', action='store_true')
    i.add_argument('--name')
    i.add_argument('--component-policy', choices=['keep', 'largest'], default='keep')
    a = p.parse_args(argv)
    out = Path(make_unique_run_dir('workflow'))
    stages, code = [], 1
    result = dict(status='fail', mode=a.mode, generation='not_tested',
                  physics='not_tested', cold_load='not_tested', render='not_tested',
                  human_webrtc='not_tested', nvidia_validation='not_tested')
    try:
        (out / 'bundle.json').write_bytes(a.bundle.read_bytes())
        bundle = json.loads((out / 'bundle.json').read_text())
        registries = {name: json.loads((ROOT / 'contracts/workflow' / file).read_text())
                      for name, file in [('capabilities', 'capabilities.json'),
                                         ('tasks', 'task_requirements.json')]}
        write_json(str(out / 'registry_snapshot.json'), registries)
        gate = evaluate(bundle, registries['capabilities']['capabilities'], registries['tasks']['tasks'])
        write_json(str(out / 'preflight.json'), gate)
        result['preflight'] = gate['status']
        stages.append({'stage': 'preflight', 'status': gate['status']})
        if a.mode == 'text':
            prompt = a.prompt_file.read_text()
            if not prompt.strip() or len(prompt) > 100000:
                raise ValueError('description must be nonempty and <=100000 characters')
            (out / 'description.txt').write_text(prompt)
            result.update(status=gate['status'], description_spec_consistency='not_tested',
                          next_action='agent selects supported authoring recipe; intake is not generation')
            code = 0 if gate['status'] == 'ready_for_planning' else 4
        else:
            if a.execute and (not a.name or not re.fullmatch(r'[A-Za-z0-9_-]+', a.name)):
                raise ValueError('--execute requires a unique safe --name')
            if a.execute and (ROOT / 'exports' / a.name).exists():
                raise ValueError('export exists; use new name before launching any generation')
            source, prepared = prepare(out / 'bundle.json', a.image, a.reference, a.license_note, 'TRIPOSR')
            stages.append({'stage': 'image_intake', 'run': source.name, 'status': prepared['status']})
            if prepared['status'] != 'prepared':
                raise ValueError('image intake not ready')
            result.update(status='prepared', intake_run=source.name)
            code = 0
            if a.execute:
                source, _ = execute_stage(out, stages, 'generate', 'pf-image-generate', source, 'generation', extra=('--component-policy', a.component_policy))
                result['generation'] = 'pass'
                source, _ = execute_stage(out, stages, 'usd_physics', 'pf-image-usd', source, 'status')
                result['physics'] = 'pass'
                source, _ = execute_stage(out, stages, 'cold_load', 'pf-image-cold', source, 'cold_live_execution')
                result['cold_load'] = 'pass'
                source, measured = execute_stage(out, stages, 'export', 'pf-image-export', source,
                                                 'status', 'exported', ('--name', a.name))
                result.update(status='pass', export_run=source.name, export_folder=measured['path'])
    except Exception as exc:
        result.update(status='fail', error=str(exc))
        code = 1
    result['exit_code'] = code
    write_json(str(out / 'result.json'), result)
    write_json(str(out / 'progress.json'), {'stages': stages, 'result': result})
    print(json.dumps({'run': str(out), **result}, indent=2))
    return code
