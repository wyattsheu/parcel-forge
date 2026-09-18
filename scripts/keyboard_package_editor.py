"""Load the latest machine-passed keyboard package in the EXISTING viewer.
Save current work and stop the timeline first. Human GUI interaction is not verified.
"""
import asyncio,json,sys,importlib
from pathlib import Path
import omni.usd
_pf_root=Path(globals().get('PF_PROJECT_ROOT', '/mnt/HDD4/wyattsheu/ITRI/parcel-forge'))
sys.path.insert(0,str(_pf_root/'src'))
import parcel_forge
parcel_forge.__path__=[str(_pf_root/'src/parcel_forge')]
if parcel_forge.__spec__ is not None:parcel_forge.__spec__.submodule_search_locations=parcel_forge.__path__
importlib.invalidate_caches()

async def _pf_keyboard_load():
    global pf_live
    import omni.timeline
    if omni.timeline.get_timeline_interface().is_playing():
        raise RuntimeError('Save work and stop timeline before loading the package.')
    matches=[]
    for folder in sorted((_pf_root/'runs').glob('*_keyboard_package'),reverse=True):
        result=folder/'result.json'
        if result.is_file():
            report=json.loads(result.read_text())
            if report.get('status')=='pass' and report.get('mobility_verified') is True:matches.append(folder)
    if not matches:raise RuntimeError('No mobility-verified free-base keyboard package run; run ./scripts/pf-keyboard-package first.')
    folder=matches[0]
    if globals().get('pf_live') is not None:pf_live.close();pf_live=None
    omni.usd.get_context().get_selection().clear_selected_prim_paths()
    ok,error=await omni.usd.get_context().open_stage_async(str(folder/'asset.usda'))
    if not ok:raise RuntimeError(error)
    from parcel_forge.carton_live import LiveCarton
    pf_live=LiveCarton(json.loads((folder/'config.json').read_text()))
    pf_live.show_controls()
    print('Loaded:',folder,'; free movable base; rigid keyboard proxy; extraction NOT TESTED.')
    print('Press Play; use native physics drag on outer flap edge. No open/close commands.')

_pf_keyboard_task=asyncio.ensure_future(_pf_keyboard_load())
def _pf_keyboard_done(task):
    if task.cancelled():return
    exc=task.exception()
    if exc is not None:
        import traceback
        traceback.print_exception(exc)
_pf_keyboard_task.add_done_callback(_pf_keyboard_done)
