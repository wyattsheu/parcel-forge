"""Run manually in the existing Isaac Script Editor after saving and stopping timeline."""
import sys,asyncio,omni.usd
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


async def _pf_start_live():
    global pf_live
    if globals().get('pf_live') is not None:
        from parcel_forge.carton_lifecycle import release_controller_references
        release_controller_references(pf_live)
        pf_live.close()
        pf_live=None
    ok,error=await omni.usd.get_context().open_stage_async('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T114330Z_ext1_carton/asset.usda')
    if not ok:raise RuntimeError(error)
    import importlib,parcel_forge.carton_live
    importlib.reload(parcel_forge.carton_live)
    from parcel_forge.carton_live import attach
    pf_live=attach('20260917T114330Z_ext1_carton')

_pf_live_task=asyncio.ensure_future(_pf_start_live())

# Retrieve own task failures instead of leaving an unhandled background exception.
def _pf_load_done(task):
    try:task.result()
    except asyncio.CancelledError:print('parcel-forge load cancelled')
    except Exception:
        import traceback
        traceback.print_exc()
_pf_live_task.add_done_callback(_pf_load_done)
