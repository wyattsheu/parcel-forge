"""Release only parcel-forge-owned Isaac6 view callbacks and USD references."""
def release_view(view):
    if view is None:return
    # Version-matched Prim has no public dispose; explicit instance-only teardown.
    view._deregister_callbacks()
    if hasattr(view,'_subscription_to_timeline_stop_event'):view._subscription_to_timeline_stop_event=None
    view._prims=[]

def release_controller_references(controller):
    release_view(getattr(controller,'view',None));controller.view=None
    probe=getattr(controller,'force_probe',None)
    if probe:
        for view in getattr(probe,'views',{}).values():release_view(view)
        probe.views={};probe.stage=None
    controller.joints={};controller.stage=None
