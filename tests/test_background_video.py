"""Offline process bookkeeping only; FAKE outputs are never render evidence."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/pf-video-background'
loader=importlib.machinery.SourceFileLoader('background_video_test_module',str(SCRIPT))
spec=importlib.util.spec_from_loader(loader.name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module)

class BackgroundVideoTests(unittest.TestCase):
    def test_worker_exception_is_completed_failure(self):
        with tempfile.TemporaryDirectory() as t:
            job=Path(t);(job/'job_request.json').write_text('malformed')
            self.assertEqual(module.worker(job),1)
            self.assertEqual(module.status_of(job)['state'],'completed')
            self.assertEqual(module.status_of(job)['result']['status'],'failed')
    def test_zero_exit_without_evidence_still_fails(self):
        with tempfile.TemporaryDirectory() as t:
            job=Path(t);module.write(job/'job_request.json',{'command':[sys.executable,'-c','print("FAKE-NO-VIDEO")']})
            self.assertEqual(module.worker(job),1)
    def test_collision_suffix_is_scanned_for_active_job(self):
        with tempfile.TemporaryDirectory() as t,patch.object(module,'RUNS',Path(t)),patch.object(module,'pid_alive',return_value=True):
            a=module.make_job_dir();b=module.make_job_dir()
            self.assertNotEqual(a,b)
            # Explicit suffixed job catches C's original glob omission.
            job=Path(t)/'fixture_background_video-1';job.mkdir()
            module.write(job/'job_request.json',{'source_run':'source'});module.write(job/'job_started.json',{'pid':123})
            self.assertEqual(module.find_active_job('source'),job)
    def test_detached_fake_completion_duplicate_and_nonzero(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);scripts=root/'scripts';scripts.mkdir();runs=root/'runs';runs.mkdir()
            shutil.copyfile(SCRIPT,scripts/SCRIPT.name)
            source=runs/'source';source.mkdir();(source/'trajectory.csv').write_text('FAKE-TRAJECTORY-NOT-PHYSICS')
            fake=scripts/'pf';fake.write_text('''#!/usr/bin/env python3
from pathlib import Path
import time,json,sys
root=Path(__file__).resolve().parents[1]
for _ in range(100):
 if (root/'release').exists():break
 time.sleep(.05)
if (root/'fail').exists():sys.exit(7)
out=root/'runs/fake_output';out.mkdir(exist_ok=True)
(out/'test_recording.mp4').write_text('FAKE-NOT-A-REAL-VIDEO')
(out/'video_result.json').write_text(json.dumps({'status':'pass','fixture':True}))
print('run:',out)
''');fake.chmod(0o755)
            command=[sys.executable,str(scripts/SCRIPT.name),'--run','source']
            first=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(first.returncode,0)
            job=Path(next(l[5:] for l in first.stdout.splitlines() if l.startswith('job: ')))
            try:
                duplicate=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(duplicate.returncode,3)
            finally:(root/'release').touch()
            for _ in range(100):
                if (job/'job_result.json').exists():break
                time.sleep(.05)
            self.assertEqual(json.loads((job/'job_result.json').read_text())['status'],'pass')
            (root/'fail').touch()
            failed=subprocess.run(command,capture_output=True,text=True);self.assertEqual(failed.returncode,0)
            job=Path(next(l[5:] for l in failed.stdout.splitlines() if l.startswith('job: ')))
            for _ in range(100):
                if (job/'job_result.json').exists():break
                time.sleep(.05)
            result=json.loads((job/'job_result.json').read_text());self.assertEqual(result['status'],'failed');self.assertEqual(result['exit_code'],7)
