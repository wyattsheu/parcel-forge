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
        # Untested precaution: a private Kit swapping assets never produced the
        # 'Unexpected reference count' warning with or without this, so it is not a
        # demonstrated fix. Our objects do form reference cycles, so collecting before
        # the stage is swapped is cheap and cannot hurt.
        import gc
        gc.collect()
    source='20260917T150447Z_ext1_carton_pull'
    # A selected prim of the outgoing stage is held by the selection and the property
    # window, and a selection gizmo also swallows the physics drag gesture. Clearing
    # our own selection before the swap addresses both and is reversible by clicking.
    try:omni.usd.get_context().get_selection().clear_selected_prim_paths()
    except Exception as exc:print('could not clear selection:',exc)
    ok,error=await omni.usd.get_context().open_stage_async('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/'+source+'/asset.usda')
    if not ok:raise RuntimeError(error)
    import parcel_forge.carton_live
    for module in ['parcel_forge.carton_lifecycle','parcel_forge.carton_force_probe','parcel_forge.carton_mouse_diagnostic','parcel_forge.carton_live']:
        importlib.reload(importlib.import_module(module))
    pf_live=parcel_forge.carton_live.attach(source,show_ui=True)
    from parcel_forge.carton_mouse_diagnostic import diagnose
    print('Passive carton: external force/contact only; no opening commands.')
    print('Rigid panels, all compliance at the creases. Measured on this asset:')
    print('  0.16 N at a major flap tip starts it opening, 0.30 N reaches 60 deg.')
    print('  Let go above the crease yield and it stays open, springing back ~5.6 deg.')
    print('  Pull with 0.05 N and it deflects and springs all the way back instead.')
    print('Measured on this asset: pushed shut it STAYS shut (springs back 0.00002 deg).')
    print('Flap angle: 0 shut, 90 straight up, 180 sticking out like a shelf, 270 folded')
    print('  right down the outside of the wall. The limit is 270; measured 268.97 after')
    print('  release, tip 99.5 mm below the crease and 1.8 mm clear of the wall face.')
    print('  Measured the way you would with a protractor at the crease, shut is 90 and')
    print('  folded right out is 359. The old asset stopped dead at 100.')
    print('The box is NOT nailed down here: it stands on the ground and slides at 0.7 N,')
    print('  while opening a flap moves it 2e-8 m. Use --base fixed to nail it again.')
    print('If yours springs open after you push it closed, you are on an older asset:')
    print('  check the "Loaded asset" line above, it must say rigid_panel_v1.')
    print('Mouse drag, if it barely moves the flap:')
    print('  1. grab near the OUTER EDGE. Halfway up the flap needs twice the force,')
    print('     a quarter of the way up needs four times it.')
    print('  2. press "Mouse: joint drag": it drags with a constraint instead of a')
    print('     force, so it does not depend on the picking force scale at all.')
    print('  3. or raise the grab strength: pf_live.grab_strength(20). Default here is')
    print('     1.0; NVIDIA\'s own Kapla demo uses 10. Restore with grab_strength(1.0).')
    print('  Push works and drag does not because the defaults are asymmetric:')
    print('  /physics/mousePush is 1000 while /physics/pickingForce is 1.0. A drag also')
    print('  needs the cursor free of the selection gizmo, which a click never fights.')
    import json as _json
    print('READ-ONLY mouse diagnosis:',_json.dumps(diagnose(),indent=1))
    print('If blockers is empty and the drag still fails: hold SHIFT for the whole drag,')
    print('or call pf_live.mouse_no_shift() to stop Shift being required.')
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
