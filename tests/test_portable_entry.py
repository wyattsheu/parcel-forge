"""Boundary tests: runtime overrides and actual stage failure signals."""
import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from parcel_forge.envprobe import load_isaac_env
from parcel_forge.workflow.entry import execute_stage

class PortableEntryTests(unittest.TestCase):
 def test_override_preserves_symlink_interpreter(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'config.json';cfg={'isaac_python':tmp+'/venv/bin/python','isaac_cwd':tmp};path.write_text(json.dumps(cfg))
   with patch.dict(os.environ,{'PF_ISAAC_CONFIG':str(path)}):self.assertEqual(load_isaac_env(),cfg)
 def test_explicit_missing_override_cannot_silently_fallback(self):
  with patch.dict(os.environ,{'PF_ISAAC_CONFIG':'/tmp/nonexistent-pf-config-1379.json'}):
   with self.assertRaises(FileNotFoundError):load_isaac_env()
 def test_zero_process_exit_does_not_prove_stage_pass(self):
  self.check_stage({'status':'fail'},0,False)
 def test_nonzero_exit_cannot_accept_pass_json(self):
  self.check_stage({'status':'pass'},1,False)
 def test_child_result_is_hash_bound_on_pass(self):
  self.check_stage({'status':'pass'},0,True)
 def check_stage(self,result,exit_code,accept):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'out';out.mkdir();child=root/'runs'/'child';child.mkdir(parents=True);(child/'result.json').write_text(json.dumps(result));stages=[]
   def run(cmd,**kw):kw['stdout'].write('run: '+str(child)+'\n');return SimpleNamespace(returncode=exit_code)
   with patch('parcel_forge.workflow.entry.ROOT',root),patch('parcel_forge.workflow.entry.subprocess.run',side_effect=run):
    if accept:
     source,_=execute_stage(out,stages,'test','fake',child,'status');self.assertEqual(source,child);self.assertEqual(len(stages[0]['result_sha256']),64)
    else:
     with self.assertRaises(ValueError):execute_stage(out,stages,'test','fake',child,'status')
     self.assertEqual(stages[0]['status'],'fail')

if __name__=='__main__':unittest.main()
