"""Run in the existing Isaac Script Editor. Save work and Stop timeline first."""
import asyncio,json
from pathlib import Path
import omni.usd

async def _pf_image_drill_load():
 import omni.timeline,carb
 root=Path(globals().get('PF_PROJECT_ROOT', '/mnt/HDD4/wyattsheu/ITRI/parcel-forge'))
 if omni.timeline.get_timeline_interface().is_playing():raise RuntimeError('Save current work and Stop before loading generated drill.')
 matches=[]
 for folder in sorted((root/'runs').glob('*_image_drill_cold'),reverse=True):
  if (folder/'result.json').exists() and (folder/'launch.json').exists():
   r=json.loads((folder/'result.json').read_text());launch=json.loads((folder/'launch.json').read_text())
   if r.get('status')=='pass' and r.get('cold_live_execution')=='pass' and launch.get('external_exit_code')==0 and (folder/'scene.usda').exists():matches.append(folder)
 if not matches:raise RuntimeError('No machine-passed generated-drill USD run yet.')
 if globals().get('pf_live') is not None:
  globals()['pf_live'].close();globals()['pf_live']=None
 folder=matches[0];omni.usd.get_context().get_selection().clear_selected_prim_paths();ok,error=await omni.usd.get_context().open_stage_async(str(folder/'scene.usda'))
 if not ok:raise RuntimeError(error)
 omni.usd.get_context().get_selection().set_selected_prim_paths(['/World/Drill'],True)
 settings=carb.settings.get_settings();settings.set_bool('/physics/mouseInteractionEnabled',True);settings.set_bool('/physics/mouseGrab',True);settings.set_bool('/physics/forceGrab',True);settings.set_float('/physics/pickingForce',50.)
 print('Generated from a real photo:',folder,'; assumed 25cm/1.5kg, whole-object rigid scope.')
 print('Press F to frame; rotate while stopped. Press Play, Shift+left mouse drag to apply force. No animation or pose commands.')

_pf_image_task=asyncio.ensure_future(_pf_image_drill_load())
def _pf_image_done(t):
 if not t.cancelled() and t.exception() is not None:
  import traceback
  traceback.print_exception(t.exception())
_pf_image_task.add_done_callback(_pf_image_done)
