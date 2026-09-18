"""Paste into the Isaac Sim Script Editor. Save your work and stop the timeline first."""
import sys,asyncio,importlib,omni.usd
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import parcel_forge
parcel_forge.__path__=[str(HERE/'parcel_forge')]
if parcel_forge.__spec__ is not None:parcel_forge.__spec__.submodule_search_locations=parcel_forge.__path__
importlib.invalidate_caches()

async def _start():
    global pf_live
    if globals().get('pf_live') is not None:
        pf_live.close();pf_live=None
        import gc;gc.collect()
    try:omni.usd.get_context().get_selection().clear_selected_prim_paths()
    except Exception as exc:print('could not clear selection:',exc)
    ok,error=await omni.usd.get_context().open_stage_async(str(HERE.parent/'carton.usda'))
    if not ok:raise RuntimeError(error)
    import json
    from parcel_forge.carton_live import LiveCarton
    pf_live=LiveCarton(json.loads((HERE.parent/'config.json').read_text()))
    pf_live.show_controls()
    print('Press Play. Without this script the creases are elastic and flaps spring back.')

_task=asyncio.ensure_future(_start())
_task.add_done_callback(lambda t:t.exception() and __import__('traceback').print_exception(t.exception()))
