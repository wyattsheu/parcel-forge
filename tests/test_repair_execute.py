import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from parcel_forge import repair_execute as execute

class RepairExecuteTests(unittest.TestCase):
    def test_gpu_selection(self):
        import subprocess
        with patch.object(execute.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'0, 100\n1, 9000\n','')):
            self.assertFalse(execute.available_gpu(0)[1]);self.assertTrue(execute.available_gpu(1)[1])

    def test_candidate_tampering(self):
        source=Path(execute.REPO_ROOT)/'runs/20260917T064621Z_s5d_repair_proposal'
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'proposal';shutil.copytree(source,out)
            execute.check_accepted(out)
            case=json.loads((out/'candidate.json').read_text());case['probe']['mass_kg']=0.001
            (out/'candidate.json').write_text(json.dumps(case))
            with self.assertRaisesRegex(ValueError,'content changed'):execute.check_accepted(out)

    def test_resource_block_never_launches(self):
        real=Path(execute.REPO_ROOT);proposal='20260917T064621Z_s5d_repair_proposal'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runs').mkdir();shutil.copytree(real/'runs'/proposal,root/'runs'/proposal)
            out=root/'runs/execution';out.mkdir()
            with patch.object(execute,'REPO_ROOT',str(root)),patch.object(execute,'make_run_dir',return_value=str(out)),patch.object(execute,'available_gpu',return_value=({0:100,1:90000},False)),patch('parcel_forge.box_host.run_case') as launch:
                self.assertEqual(execute.main(['--proposal-run',proposal]),4);launch.assert_not_called()
            self.assertTrue((out/'blocked.json').is_file())
            self.assertEqual(json.loads((out/'execution_result.json').read_text())['status'],'blocked')

    def test_rejected_proposal_never_checks_gpu(self):
        real=Path(execute.REPO_ROOT);proposal='20260917T064621Z_s5d_repair_proposal'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runs').mkdir();shutil.copytree(real/'runs'/proposal,root/'runs'/proposal)
            p=root/'runs'/proposal/'proposal_result.json';r=json.loads(p.read_text());r['status']='rejected';p.write_text(json.dumps(r))
            out=root/'runs/execution';out.mkdir()
            with patch.object(execute,'REPO_ROOT',str(root)),patch.object(execute,'make_run_dir',return_value=str(out)),patch.object(execute,'available_gpu') as gpu:
                self.assertEqual(execute.main(['--proposal-run',proposal]),1);gpu.assert_not_called()
