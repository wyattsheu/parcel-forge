"""Manual passive carton loader: save work and stop timeline first."""
import sys,asyncio,importlib,omni.usd
sys.path.insert(0,'/mnt/HDD4/wyattsheu/ITRI/parcel-forge/src')

# Long-lived Kit may have cached another parcel_forge or a negative directory lookup.
from pathlib import Path
_pf_package_dir=Path('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge')
if not (_pf_package_dir/'carton_lifecycle.py').is_file():
    raise FileNotFoundError('Viewer cannot see repository module: '+str(_pf_package_dir/'carton_lifecycle.py'))
import parcel_forge
parcel_forge.__path__=[str(_pf_package_dir)]
if parcel_forge.__spec__ is not None:
    parcel_forge.__spec__.submodule_search_locations=parcel_forge.__path__
import importlib
importlib.invalidate_caches()
print('parcel-forge module search:',list(parcel_forge.__path__))


async def _pf_start_passive():
    global pf_live
    if globals().get('pf_live') is not None:
        from parcel_forge.carton_lifecycle import release_controller_references
        release_controller_references(pf_live)
        pf_live.close()
        pf_live=None
    source='20260917T123830Z_ext1_independent_interaction'
    ok,error=await omni.usd.get_context().open_stage_async('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/'+source+'/asset.usda')
    if not ok:raise RuntimeError(error)
    import parcel_forge.carton_live
    for module in ['parcel_forge.carton_lifecycle','parcel_forge.carton_force_probe','parcel_forge.carton_mouse_diagnostic','parcel_forge.carton_live']:
        importlib.reload(importlib.import_module(module))
    pf_live=parcel_forge.carton_live.attach(source,show_ui=False)
    from parcel_forge.carton_mouse_diagnostic import diagnose
    print('Passive carton: external force/contact only; no opening commands.')
    print('READ-ONLY mouse diagnosis:',diagnose())
    print('Press Play to run material callback. Native Shift-drag not verified.')

if '_pf_live_task' in globals() and not _pf_live_task.done():
    raise RuntimeError('Previous parcel-forge load still pending; wait before executing again.')
_pf_live_task=asyncio.ensure_future(_pf_start_passive())

# Retrieve own task failures instead of leaving an unhandled background exception.
def _pf_load_done(task):
    try:task.result()
    except asyncio.CancelledError:print('parcel-forge load cancelled')
    except Exception:
        import traceback
        traceback.print_exc()
_pf_live_task.add_done_callback(_pf_load_done)
