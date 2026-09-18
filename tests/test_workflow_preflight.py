import unittest
import json
from copy import deepcopy
from pathlib import Path
from parcel_forge.workflow.preflight import evaluate

ROOT = Path(__file__).resolve().parents[1]

class PreflightTests(unittest.TestCase):
    def setUp(self):
        base = ROOT/'contracts/workflow'
        self.caps=json.loads((base/'capabilities.json').read_text())['capabilities']
        self.tasks=json.loads((base/'task_requirements.json').read_text())['tasks']
        self.b=json.loads((base/'examples/carton.json').read_text())
    def run_case(self,b=None): return evaluate(self.b if b is None else b,self.caps,self.tasks)
    def test_missing_input(self): self.assertEqual(self.run_case()['status'],'needs_input')
    def test_unknown_field(self):
        self.b['typo']=1;self.assertEqual(self.run_case()['status'],'conflict')
    def test_nonfinite(self):
        self.b['parameter_cards'][0]['value']=float('nan');self.assertEqual(self.run_case()['status'],'conflict')
    def test_missing_runtime(self):
        self.b['asset_contract']['runtime_requirements']=[];self.assertEqual(self.run_case()['status'],'conflict')
    def test_missing_check(self):
        self.b['validation_plan']['required_checks'].remove('behavior.plastic_crease');self.assertEqual(self.run_case()['status'],'conflict')
    def test_broken_interface(self):
        self.b['assembly_graph']['interfaces'][0]['a']='ghost';self.assertEqual(self.run_case()['status'],'conflict')
    def test_task_change_adds_release_requirement(self):
        self.b['task_brief']['intended_task']='unwrap'
        result=self.run_case();self.assertIn('peelable_bond',result['required_behaviors']);self.assertEqual(result['status'],'conflict')
    def test_never_grants_generation(self): self.assertFalse(self.run_case()['generation_authorized'])
    def test_supported_complete_is_planning_only(self):
        self.b['task_brief']['initial_state']='tape_removed';p=self.b['parameter_cards'][0];p.update(value=.2,provenance='assumed')
        self.assertEqual(self.run_case()['status'],'ready_for_planning');self.assertEqual(self.run_case()['physics_execution'],'not_tested')
    def test_unknown_version(self):
        self.b['schema']='parcel_forge.case/1';self.assertEqual(self.run_case()['status'],'conflict')
    def test_declaring_physics_pass_rejected(self):
        self.b['validation_plan']['check_status']='pass';self.assertEqual(self.run_case()['status'],'conflict')

    def test_movable_prop_requires_mobility_check(self):
        self.b['validation_plan']['required_checks'].remove('structure.mobility')
        self.assertEqual(self.run_case()['status'],'conflict')
    def test_package_extraction_rejects_world_fixture(self):
        self.b['task_brief'].update(intended_task='open_and_extract',base_mode='fixed')
        self.assertTrue(any(x['reason']=='robot_prop_must_be_movable' for x in self.run_case()['errors']))
