"""Acceptance must not inherit a fault-regression pass or changed evidence."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
from parcel_forge.upstream_bridge import FILES, digest, evaluate
ROOT = Path(__file__).resolve().parents[1]

class TestAcceptanceBridge(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def fixture(self, fault=False):
        case = json.loads((ROOT/'cases/open_box_normal.json').read_text())
        if fault:
            case['geometry']['fault'] = 'missing_bottom'
            case['expected_outcome'] = 'fell_through'
        profile = json.loads((ROOT/'profiles/open_box_v1.json').read_text())
        profile['simulation']['steps'] = 2
        for name, value in [('request.json',case),('profile.json',profile),
            ('s2_result.json',{'physics':{'status':'ran'},'summary':{'verdict':'pass',
             'observed_outcome':'fell_through' if fault else 'inside'}})]:
            (self.path/name).write_text(json.dumps(value))
        (self.path/'asset.usda').write_text('test placeholder; USD not judged by this unit test')
        local_z = -0.18 if fault else 0.025
        rows = [{'step':step,'sim_time_s':step*profile['simulation']['dt'],
            'px_m':0,'py_m':0,'pz_m':local_z+0.2,'local_x_m':0,'local_y_m':0,
            'local_z_m':local_z,'vx_mps':0,'vy_mps':0,'vz_mps':0}
            for step in (1,2)]
        with (self.path/'trajectory.csv').open('w') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        manifest={'external_exit_code':0,'inputs_sha256':{'case':digest(self.path/'request.json')},
                  'profile_sha256':digest(self.path/'profile.json'),
                  'asset_sha256':digest(self.path/'asset.usda')}
        (self.path/'manifest.json').write_text(json.dumps(manifest))
        return {name:digest(self.path/name) for name in FILES}

    def test_normal_accepts(self):
        self.assertEqual(evaluate(self.path,self.fixture())['task_acceptance'],'pass')

    def test_fault_regression_pass_cannot_accept_asset(self):
        result=evaluate(self.path,self.fixture(True))
        self.assertEqual(result['source_regression_verdict'],'pass')
        self.assertEqual(result['regression_expectation'],'pass')
        self.assertEqual(result['simulation_execution'],'pass')
        self.assertEqual(result['task_acceptance'],'fail')

    def test_bound_trajectory_tampering_rejected(self):
        hashes=self.fixture();p=self.path/'trajectory.csv';p.write_text(p.read_text().replace('0.025','0.075'))
        with self.assertRaises(ValueError):evaluate(self.path,hashes)

    def test_changed_profile_cannot_rebind_original_manifest(self):
        hashes=self.fixture();p=self.path/'profile.json';p.write_text(p.read_text()+' ')
        hashes['profile.json']=digest(p)
        with self.assertRaises(ValueError):evaluate(self.path,hashes)

    def test_missing_measurements_rejected(self):
        hashes=self.fixture();(self.path/'trajectory.csv').unlink()
        with self.assertRaises(FileNotFoundError):evaluate(self.path,hashes)
