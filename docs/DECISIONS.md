# Decisions

Append-only. A superseded decision keeps its entry and gains a "Superseded by"
line; it is never deleted.

## D001 - Use the Isaac Sim standalone launcher, not Isaac Lab's AppLauncher

Status: accepted
Reason: `IsaacSim_From_Zero_Start_Here.md` section 3 requires that the project
depend only on the installed Isaac Sim runtime, and section 5 forbids mixing two
launchers. Isaac Lab 16.4.0 happens to live in the same venv, but depending on it
would make every later report Isaac-Lab-shaped.
Alternative: `isaaclab.app.AppLauncher`, which the machine's existing WebRTC
viewer script uses. Rejected for this project, not removed from the machine.
Consequence: We construct `isaacsim.SimulationApp` ourselves and drive physics
with `SimulationManager`. If Isaac Lab is ever needed, it arrives as a second
runtime adapter, not as a rewrite.
Evidence: `runs/<s1 run>/logs/isaac_runtime.log`, `src/parcel_forge/runtime/isaacsim_runtime.py`.
Revisit when: A task card needs Isaac Lab environments, learning or batch cloning.

## D002 - Target the Isaac Sim 6.0 experimental core API

Status: accepted
Reason: This install is 6.0.1.0, where the 4.x `isaacsim.core.api`
(`World`, `DynamicCuboid`, `SimulationContext`) no longer exists. Verified by
listing `site-packages/isaacsim/exts`: only `isaacsim.core.experimental.*` and
`isaacsim.core.simulation_manager` are present.
Alternative: Pinning to older tutorial APIs. Impossible without changing the
install, which is forbidden.
Consequence: Pose and velocity read-back goes through
`isaacsim.core.experimental.prims.RigidPrim` (tensor backend, quaternion returned
as w,x,y,z); stepping goes through `SimulationManager.step(steps=...)`.
Evidence: S1 run trajectory and `docs/ENVIRONMENT.md`.
Revisit when: The installed version changes (it must not change on our account).

## D003 - Livestream stays disabled in every parcel-forge run

Status: accepted
Reason: The user has a live WebRTC viewer holding the signaling port. Enabling
livestream would collide with it, and the from-zero brief forbids disturbing the
working session.
Alternative: Reusing the existing viewer's ports after stopping it. Rejected:
we never stop someone else's process.
Consequence: parcel-forge produces offline PNG evidence instead. WebRTC viewing
stays a separate, human-only verification channel, always reported as
`not_tested` in agent output.
Evidence: `config/isaac_env.json` `do_not_touch`, doctor check `webrtc_session_untouched`.
Revisit when: The user explicitly wants a parcel-forge-owned viewer on different ports.

## D004 - PNG encoding uses the standard library, not Pillow

Status: accepted
Reason: The brief says to prefer the standard library and to install nothing into
the Isaac runtime. `zlib` + `struct` encode an 8-bit PNG in ~30 lines.
Alternative: Pillow or `capture_viewport_to_file`. The latter is asynchronous and
harder to bind to a specific physics state.
Consequence: `src/parcel_forge/pngio.py` owns the encoder and also computes the
blank-frame statistic used to fail black renders.
Evidence: `runs/<s1 run>/renders/scene_final.png` and its `image_stats`.
Revisit when: We need EXR, depth or multi-channel annotator output.

## D005 - Ground plane is a physics `UsdGeomPlane` plus a separate visual slab

Status: accepted
Reason: `UsdGeomPlane` is infinite for collision but has no renderable surface,
which produced a floorless image. Splitting collision from visual keeps the
physics exact while giving the evidence render a visible floor.
Alternative: A large thin collision cube. Rejected: it introduces a second
contact surface and an arbitrary thickness into the physics result.
Consequence: The visual slab carries no collider and sits below z=0; any future
check must read the collider, not the slab.
Evidence: S1 render and `S1.cube_rests_on_ground` (final z = half edge length).
Revisit when: S2 introduces the box, whose walls need both roles on one prim.

## D006 - The probe outcome is judged in the box local frame

Status: accepted
Reason: The test box floats 0.20 m above the world floor. In the missing-bottom
fault the probe still comes to rest on a solid surface, so in world coordinates it
looks supported (z = 0.02 m) and the fault would pass. In box local coordinates the
same state reads z = -0.18 m, clearly below the box. Judging in world Z would make
the whole fault suite blind.
Alternative: Comparing against the world floor height. Rejected: it conflates "the
box held it" with "something held it".
Consequence: `validation/outcome.py` takes local coordinates only, and the runtime
adapter exposes `world_to_local()` via the composed USD transform.
Evidence: `runs/20260916T053320Z_s2_open_box_no_bottom/` (local z = -0.18000) and
`tests/test_outcome.py::test_probe_on_the_world_floor_is_fell_through_not_inside`.
Revisit when: A box is allowed to tilt or move (S4 dynamic box); the local frame
then follows the box, which is exactly what is wanted.

## D007 - Two evidence views per S2 case

Status: accepted
Reason: A single side view rendered the box correctly but hid the probe behind a
wall, so the picture could not corroborate the verdict. No single camera can show
all three expected resting places (interior floor, sealed mouth, world floor
beneath a floating box).
Alternative: One view plus trusting the numbers. Rejected: evidence should show the
thing being judged.
Consequence: `profiles/open_box_v1.json` carries a `views` list (`interior_top`,
`side_low`); the render check fails if any view is blank. Only framing changed; no
acceptance tolerance was touched, and verdicts are unaffected by camera placement.
Evidence: `renders/*_interior_top.png` and `renders/*_side_low.png` in each S2 run.
Revisit when: S6 adds multi-view VLM review, which will need a named view set.
