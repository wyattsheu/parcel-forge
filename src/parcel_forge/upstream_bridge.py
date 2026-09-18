"""Thin evidence bridge: upstream USD sanity plus independent ITRI containment."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

from .evidence import REPO_ROOT, make_run_dir, write_json
from .geometry import geometry_manifest
from .validation.outcome import classify_probe_outcome

FILES = ('request.json', 'profile.json', 's2_result.json', 'manifest.json',
         'trajectory.csv', 'asset.usda')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def evaluate(directory, hashes):
    """Recompute task result from frozen measurements; never trust regression pass."""
    directory = Path(directory)
    for name in FILES:
        if name not in hashes or digest(directory / name) != hashes[name]:
            raise ValueError(f'missing or changed evidence: {name}')
    case, profile, result, manifest = [json.loads((directory / name).read_text())
        for name in FILES[:4]]
    if case['intended_task'] != 'place_object_inside':
        raise ValueError('unsupported intended_task')
    for filename, expected in [('request.json', manifest['inputs_sha256']['case']),
                               ('profile.json', manifest['profile_sha256']),
                               ('asset.usda', manifest['asset_sha256'])]:
        if hashes[filename] != expected:
            raise ValueError(f'original manifest mismatch: {filename}')
    if manifest['external_exit_code'] != 0 or result['physics']['status'] != 'ran':
        raise ValueError('source physics execution incomplete')
    with (directory / 'trajectory.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != profile['simulation']['steps']:
        raise ValueError('trajectory step count mismatch')
    previous = None
    box_z = case['placement']['box_outer_bottom_above_world_floor_m']
    for step, row in enumerate(rows, 1):
        if int(row['step']) != step or not all(math.isfinite(float(v)) for v in row.values()):
            raise ValueError('invalid trajectory sample')
        time = float(row['sim_time_s'])
        if previous is not None and abs(time - previous - profile['simulation']['dt']) > 2e-6:
            raise ValueError('trajectory time spacing mismatch')
        previous = time
        if any(abs(float(row[w]) - offset - float(row[l])) > 1e-7
               for w, l, offset in [('px_m','local_x_m',0), ('py_m','local_y_m',0),
                                     ('pz_m','local_z_m',box_z)]):
            raise ValueError('world/local trajectory mismatch')
    final = rows[-1]
    geom = geometry_manifest(case['geometry']['outer_size_m'],
                             case['geometry']['wall_thickness_m'], case['geometry']['fault'])
    outcome = classify_probe_outcome(
        [float(final[k]) for k in ('local_x_m','local_y_m','local_z_m')],
        math.sqrt(sum(float(final[k])**2 for k in ('vx_mps','vy_mps','vz_mps'))),
        min(float(row['local_z_m']) for row in rows),
        geom['wall_thickness_m'], case['probe']['size_m'], geom['interior_length_m'],
        geom['interior_width_m'], profile['tolerances'])
    if outcome['outcome'] != result['summary']['observed_outcome']:
        raise ValueError('recomputed outcome disagrees with source report')
    return {'simulation_execution': 'pass',
            'task_acceptance': 'pass' if outcome['outcome'] == 'inside' else 'fail',
            'regression_expectation': 'pass' if outcome['outcome'] == case['expected_outcome'] else 'fail',
            'outcome': outcome, 'case_id': case['case_id'], 'samples': len(rows),
            'source_regression_verdict': result['summary']['verdict']}

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    args = parser.parse_args(argv)
    source = (Path(REPO_ROOT) / 'runs' / args.run).resolve()
    run_dir = Path(make_run_dir('s5b_upstream_bridge'))
    result = {'schema':'parcel_forge.upstream_bridge/1', 'source_run':args.run,
              'overall_acceptance':'insufficient_evidence', 'errors':[],
              'render':'not_tested', 'webrtc_human_view':'not_tested'}
    exit_code = 4
    try:
        if source.parent != (Path(REPO_ROOT) / 'runs').resolve() or not source.is_dir():
            raise ValueError('source must be a run directory in this repository')
        frozen = run_dir / 'inputs'; frozen.mkdir()
        for name in FILES:
            shutil.copyfile(source / name, frozen / name)
        hashes = {name:digest(frozen / name) for name in FILES}
        write_json(str(run_dir / 'evidence_hashes.json'), hashes)
        result['itri'] = evaluate(frozen, hashes)
        config = json.loads((Path(REPO_ROOT) / 'config/upstream_content_agents.json').read_text())
        root = (Path(REPO_ROOT) / config['checkout']).resolve()
        actual_sha = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        if actual_sha != config['commit'] or subprocess.check_output(
                ['git','-C',str(root),'status','--porcelain'],text=True).strip():
            raise ValueError('upstream commit changed or source dirty')
        command = [str(Path(REPO_ROOT) / config['environment'] / 'bin/validation-agent'), 'validate',
                   '--task','Check authored physics sanity', '--template','physics_sane',
                   '--output-dir',str(run_dir / 'upstream'),str(frozen / 'asset.usda')]
        env = dict(os.environ, WU_OVRTX_AUTO_PROVISION='0')
        for key in list(env):
            if key.endswith(('API_KEY','TOKEN','SECRET')): env.pop(key,None)
        with (run_dir / 'upstream.log').open('w') as log:
            completed = subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        write_json(str(run_dir / 'upstream_command.json'),
                   {'command':command,'cwd':str(root),'exit_code':completed.returncode})
        official = json.loads((run_dir / 'upstream/validation_result.json').read_text())
        result['upstream'] = {'commit':actual_sha,'template':'physics_sane',
                              'verdict':official['verdict'],'exit_code':completed.returncode}
        # Recheck bound bytes after the external tool ran.
        evaluate(frozen, hashes)
        if completed.returncode == 0 and official['verdict'] == 'pass':
            result['overall_acceptance'] = result['itri']['task_acceptance']
            exit_code = 0 if result['overall_acceptance'] == 'pass' else 1
        else:
            result['overall_acceptance'] = 'fail' if official['verdict'] == 'fail' else 'insufficient_evidence'
            exit_code = 1 if result['overall_acceptance'] == 'fail' else 4
    except Exception as exc:
        result['errors'].append({'type':type(exc).__name__,'message':str(exc)})
    result['exit_code'] = exit_code
    write_json(str(run_dir / 'bridge_result.json'),result)
    (run_dir / 'summary.md').write_text('# S5-B upstream bridge\n\n'+json.dumps(result,indent=2)+'\n')
    print(f'run: {run_dir}')
    print(json.dumps(result,indent=2))
    return exit_code
