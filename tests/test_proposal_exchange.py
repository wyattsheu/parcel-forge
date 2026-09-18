import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from parcel_forge import proposal_exchange as exchange


class ProposalExchangeTests(unittest.TestCase):
    def test_strict_json(self):
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}',b'```json\n{}\n```',b'{} trailing',b' '*65537]:
            with self.subTest(raw=raw[:30]),self.assertRaises(ValueError):exchange.strict_json(raw)
        self.assertEqual(exchange.strict_json(b'{"a":1}'),{'a':1})

    def test_exchange_and_rejections(self):
        real=Path(exchange.REPO_ROOT);source='20260917T000106Z_s2_open_box_sealed'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runs').mkdir()
            shutil.copytree(real/'runs'/source,root/'runs'/source)
            counter=iter(range(30))
            def make(prefix):
                out=root/'runs'/f'fixture_{next(counter)}_{prefix}';out.mkdir();return str(out)
            with patch.object(exchange,'REPO_ROOT',str(root)),patch.object(exchange,'make_run_dir',make):
                code,prompt,meta=exchange.prepare(source)
                self.assertEqual(code,0);self.assertFalse(meta['attempt_reserved'])
                answer=dict(meta['context'],schema='parcel_forge.repair_proposal/2',changes=[{'path':'/geometry/fault','from':'sealed_lid','to':'none'}])
                response=root/'runs'/'answer.json';response.write_text(json.dumps(answer))
                code,out,result=exchange.check_response(prompt.name,response)
                self.assertEqual(code,0);self.assertEqual((out/'proposal.json').read_bytes(),response.read_bytes())
                self.assertEqual(result['model_execution'],'unknown')
                self.assertEqual(list((root/'runs').glob('**/attempt_receipt.json')),[])
                answer['changes'][0]['path']='/probe/size_m';response.write_text(json.dumps(answer))
                code,out,result=exchange.check_response(prompt.name,response)
                self.assertEqual(code,1);self.assertFalse((out/'proposal.json').exists())
                response.unlink();response.symlink_to(root/'runs'/source/'request.json')
                code,out,result=exchange.check_response(prompt.name,response)
                self.assertEqual(code,1);self.assertIn('symlink',result['reason'])
                (prompt/'prompt.txt').write_text('tampered')
                code,out,result=exchange.check_response(prompt.name,response)
                self.assertEqual(code,1);self.assertEqual(result['reason'],'prompt changed')

    def test_budget_exhausted(self):
        real=Path(exchange.REPO_ROOT);source='20260917T000106Z_s2_open_box_sealed'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'runs').mkdir();shutil.copytree(real/'runs'/source,root/'runs'/source)
            hash=exchange.digest(root/'runs'/source/'request.json')
            for attempt in range(1,4):
                p=root/'runs'/f'fixture_{attempt}_s5d_repair_proposal';p.mkdir()
                (p/'attempt_receipt.json').write_text(json.dumps({'source_run':source,'source_spec_sha256':hash,'attempt':attempt}))
            out=root/'runs'/'prompt';out.mkdir()
            with patch.object(exchange,'REPO_ROOT',str(root)),patch.object(exchange,'make_run_dir',return_value=str(out)):
                code,_,result=exchange.prepare(source)
                self.assertEqual(code,1);self.assertEqual(result['reason'],'budget_exhausted');self.assertFalse((out/'prompt.txt').exists())
