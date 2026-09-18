import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from parcel_forge.repair_guard import apply_proposal,submit,allowed_file
from parcel_forge.repair_link import verify_link

ROOT=Path(__file__).resolve().parents[1]
class RepairGuardTests(unittest.TestCase):
    def case(self,name):return json.loads((ROOT/'cases'/f'{name}.json').read_text())
    def proposal(self,name):return json.loads((ROOT/'contracts/repair_proposals'/f'{name}.json').read_text())
    def apply(self,source,proposal):
        context=self.proposal('restore_bottom' if source['case_id']=='open_box_no_bottom' else 'remove_lid')
        return apply_proposal(source,proposal,source_run=context['source_run'],source_spec_sha256=context['source_spec_sha256'],attempt=1)
    def test_repairs_preserve_every_other_field_and_source(self):
        for case,proposal in [('open_box_sealed','remove_lid'),('open_box_no_bottom','restore_bottom')]:
            source=self.case(case);original=copy.deepcopy(source)
            candidate=self.apply(source,self.proposal(proposal))
            self.assertEqual(source,original);candidate['geometry']['fault']=source['geometry']['fault'];self.assertEqual(candidate,source)
    def test_protected_fields_rejected(self):
        for path in ['/probe/size_m','/probe/mass_kg','/expected_outcome','/intended_task','/seed','/physics/collider','/geometry/outer_size_m','/profile/tolerances']:
            p=self.proposal('remove_lid');p['changes'][0]['path']=path
            with self.assertRaises(ValueError):self.apply(self.case('open_box_sealed'),p)
        with self.assertRaises(ValueError):self.apply(self.case('open_box_sealed'),self.proposal('reject_probe_change'))
    def test_stale_and_extra_changes_rejected(self):
        with self.assertRaises(ValueError):self.apply(self.case('open_box_sealed'),self.proposal('restore_bottom'))
        p=self.proposal('remove_lid');p['changes'].append(copy.deepcopy(p['changes'][0]))
        with self.assertRaises(ValueError):self.apply(self.case('open_box_sealed'),p)
    def test_noop_and_task_mismatch_rejected(self):
        with self.assertRaises(ValueError):self.apply(self.case('open_box_normal'),self.proposal('remove_lid'))
        source=self.case('open_box_sealed');source['intended_task']='another_task'
        with self.assertRaises(ValueError):self.apply(source,self.proposal('remove_lid'))
    def test_binding_attempt_and_legacy_rejected(self):
        for key,value in [('schema','parcel_forge.repair_proposal/1'),('source_run','other'),('source_spec_sha256','0'*64),('attempt',True),('attempt',4),('attempt',2)]:
            p=self.proposal('remove_lid');p[key]=value
            with self.assertRaises(ValueError):self.apply(self.case('open_box_sealed'),p)
    def test_paths_budget_and_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'runs').mkdir();(root/'contracts/repair_proposals').mkdir(parents=True)
            proposal=self.proposal('restore_bottom');source=proposal['source_run']
            shutil.copytree(ROOT/'runs'/source,root/'runs'/source)
            path=root/'contracts/repair_proposals/proposal.json';results=[]
            for attempt in range(1,5):
                proposal['attempt']=attempt;path.write_text(json.dumps(proposal))
                code,out,result=submit(source,path,root=root);results.append(out)
                self.assertEqual(code,0 if attempt<=3 else 1)
            self.assertIn('budget_exhausted',result['reason'])
            # Actor cannot reset count by submitting attempt=1 again.
            proposal['attempt']=1;path.write_text(json.dumps(proposal));self.assertEqual(submit(source,path,root=root)[0],1)
            after=root/'runs/after_fixture';shutil.copytree(ROOT/'runs/20260917T015711Z_s2_open_box_no_bottom',after)
            self.assertEqual(verify_link(results[0],after)['task_gate']['task_acceptance'],'pass')
            (after/'request.json').write_text('{}')
            with self.assertRaises(ValueError):verify_link(results[0],after)
            link=root/'contracts/repair_proposals/link.json';link.symlink_to(path)
            with self.assertRaises(ValueError):allowed_file(link,root,['contracts/repair_proposals'])
            with self.assertRaises(ValueError):allowed_file(ROOT/'profiles/open_box_v1.json',root,['runs'])
