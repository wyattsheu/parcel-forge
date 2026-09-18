"""Read-only report on whether a physics mouse drag can happen at all.

Read from the installed omni.physx.ui 110.1.13: a drag reaches PhysX only through
PhysxUIViewportOverlays.on_mouse_shift_drag_start, which returns early unless the
extension is running, the timeline is playing, Shift is held (or the interaction
state is overridden) and no other gesture or hover owns the cursor. Nothing here
enables, sets or installs anything.
"""

def _instance():
    try:
        from omni.physxui.scripts.extension import get_physicsui_instance
        return get_physicsui_instance()
    except Exception as exc:
        return exc


def diagnose():
    import omni.kit.app,carb
    manager=omni.kit.app.get_app().get_extension_manager();settings=carb.settings.get_settings()
    extensions={n:manager.is_extension_enabled(n) for n in ['omni.physics.ui','omni.physics.physx.ui','omni.physx.ui']}
    instance=_instance();present=not isinstance(instance,Exception) and instance is not None
    overlays=getattr(instance,'_viewport_overlays',None) if present else None
    state=getattr(overlays,'_mouse_interaction_state',None)
    try:
        from omni.timeline import get_timeline_interface
        playing=bool(get_timeline_interface().is_playing())
    except Exception:playing=None
    report={'extensions_enabled':extensions,
            'physx_ui_instance_present':present,
            'viewport_overlays_present':overlays is not None,
            'mouse_interaction_state':str(state),
            'timeline_playing':playing,
            'mouse_settings':{k:settings.get(k) for k in ['/physics/mouseInteractionEnabled','/physics/mouseGrab','/physics/forceGrab','/physics/pickingForce','/physics/mousePush']},
            'scope':'read_only; nothing enabled, set or installed'}
    blockers=[]
    if not extensions.get('omni.physx.ui'):blockers.append('omni.physx.ui is not enabled: this application has no physics mouse drag at all, and the picking force is irrelevant')
    if not present:blockers.append('the physx UI extension object is absent, so no viewport gesture is registered')
    elif overlays is None:blockers.append('the extension is up but owns no viewport overlay, so no drag gesture is attached to a viewport')
    if playing is False:blockers.append('the timeline is not playing: the drag handler returns immediately unless it is')
    if not settings.get('/physics/mouseInteractionEnabled'):blockers.append('/physics/mouseInteractionEnabled is off')
    report['blockers']=blockers
    report['verdict']='no blocker found in this read-only check; if the drag still does nothing, hold Shift while dragging, click away from the selection gizmo, and grab the outer edge of the flap' if not blockers else 'mouse drag cannot work until these are resolved'
    report['shift_required']='Shift must be held for the whole drag unless mouse_interaction_state is ENABLED'
    return report
