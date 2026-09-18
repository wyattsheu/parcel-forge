from pathlib import Path
import asyncio,omni.usd,omni.timeline
async def _load():
 if omni.timeline.get_timeline_interface().is_playing():raise RuntimeError('Save and Stop timeline first')
 ok,error=await omni.usd.get_context().open_stage_async(str(Path(PF_ASSET_FOLDER)/'scene.usda'))
 if not ok:raise RuntimeError(error)
 omni.usd.get_context().get_selection().set_selected_prim_paths(['/World/Drill'],True)
 print('Press F, inspect while stopped; then Play. Whole-object rigid asset.')
_task=asyncio.ensure_future(_load())
def _done(t):
 if not t.cancelled() and t.exception() is not None:
  import traceback
  traceback.print_exception(t.exception())
_task.add_done_callback(_done)
