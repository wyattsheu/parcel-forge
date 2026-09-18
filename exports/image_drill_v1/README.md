# Image-generated cordless drill

Open scene.usda in Isaac6.0.1, or reference asset.usda (default /Drill) into your physics world. Metres/Z up; vertex colors, no required Python material controller. Maximum bbox dimension .25m and total mass1.5kg are assumptions, not this pictured drill's calibration. PhysX convexDecomposition; shape/contact fidelity pending human/measurement checks. No trigger/motor articulation.

Cold physics/readback pass is recorded in validation.json. WebRTC/render not_tested. Save work and Stop before opening scene. Select /World/Drill and F; Play, then native force drag (Shift+left mouse when enabled). No pose animation.

Script Editor portable loader: set PF_ASSET_FOLDER to this directory, then exec the contents of load_in_isaacsim.py.
