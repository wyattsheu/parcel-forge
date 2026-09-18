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

## D008 - Build and validate run on pxr alone, without starting Kit

Status: accepted
Reason: Measured on this install: `from pxr import Usd` inside the Isaac venv costs
about 2.6 s and no GPU, while `SimulationApp` costs 15-190 s and a GPU context.
Authoring a USD file and re-reading it needs only OpenUSD.
Alternative: Routing every subcommand through `SimulationApp`, as S1/S2 do.
Rejected: it would make the 13-case schema/geometry suite take ten minutes and
compete with the user's WebRTC session for the GPU.
Consequence: `pf build`, `pf validate` and `pf verify` use the Isaac interpreter but
never construct `SimulationApp`; the whole 13-case suite runs in ~4 s. Only
`pf smoke` and `pf box` need the simulator. A static pass therefore says nothing
about PhysX cooking, which is exactly why `pf box` still exists.
Evidence: `runs/*_s3_verify_*/logs/build.log` (no Kit banner) and the 4.2 s wall
time of `./scripts/pf verify --all`.
Revisit when: A check genuinely needs PhysX, for example collider cooking or
read-back of solver-resolved mass properties (S4).

## D009 - Invalid case files live in cases/invalid/ with a sidecar expectation file

Status: accepted
Reason: The invalid specifications must stay exactly as invalid as they claim, so
they cannot carry an `expected_error` field: the schema would reject that field as
unknown, and the case would then be rejected for the wrong reason.
Alternative: An `expected_error` key inside each file. Rejected for the reason above.
Consequence: `cases/invalid/expected_errors.json` maps case id to the error class
that must fire. `pf box --all` globs `cases/*.json` and so never tries to simulate
an invalid spec; `pf verify --all` covers both directories.
Evidence: `runs/*_s3_verify_bad_*/schema_findings.json` and the S3 suite table.
Revisit when: A case needs to assert several error classes at once.

## D010 - Run NVIDIA's official USD validator, and prove it can fail

Status: accepted
Reason: `IsaacSim_Asset_Workflow_Handbook.md` section 3 points at NVIDIA USD Content
Agents for a validation entry point. That project is not installable here, but the
validator it wraps, `omni.asset_validator.core` 1.19.3, ships inside this Isaac Sim
install and imports without Kit, so it fits the fast pxr-only path (D008). Our own
G1 rules were written by the same agent that wrote the generator, which is exactly
the situation an external rule set exists to correct.
Alternative: Continuing to report the check as `blocked`. Rejected once the validator
was found to be present and runnable.
Consequence: `pf verify` runs 41 official rules on every built asset. Official and
internal coverage are reported separately in `validation.json`; neither is described
as a SimReady certification, because no SimReady profile was requested. A companion
check, `G7.official_validator_can_fail`, runs the engine against a deliberately broken
fixture (no defaultPrim, Gprim nested inside a Gprim) and fails the run if the engine
reports it clean — a validator that cannot fail makes its own clean verdict worthless.
Evidence: `runs/20260916T0935*_s3_verify_*/validation.json`; the self-test reports
DefaultPrimChecker, PrimEncapsulationChecker and StageMetadataChecker firing.
Revisit when: A SimReady profile is genuinely required, or the install changes.

## D011 - Version-matched API lookup becomes a tool, not a habit

Status: accepted, not yet implemented
Reason: LL3M reports that retrieval over *version-specific* API documentation cut
error rates by 26%. This project hit the same problem on day one: Isaac Sim 6.0.1
removed `isaacsim.core.api`, so every 4.x tutorial and every recalled example is
wrong here. That was solved by reading local `site-packages`, but only because the
agent happened to check.
Alternative: Trusting model recall or web tutorials. Demonstrably wrong on this install.
Consequence: A small local lookup tool over the installed `isaacsim` source and its
extension docs, so any future session resolves an API against *this* version before
writing code. Until it exists, `docs/ENVIRONMENT.md` carries the API shape explicitly.
Evidence: D002, and the S1 adapter written from local source.
Revisit when: The tool exists; then this decision records its scope.

## D012 - A model-based critic may never upgrade a verdict

Status: accepted, binding on S5 and S6
Reason: Articulate-Anything reports that its critic's dominant error is the **false
positive** — declaring an incorrect articulation correct, on "difficult-to-notice
errors". A pipeline whose gate is a model opinion inherits that failure directly.
Alternative: Using a critic rating as the acceptance signal, as the paper does with a
0-10 realism score and a threshold of 5. Rejected as a gate; acceptable as triage.
Consequence: Deterministic measurements own pass/fail. A critic may only propose a
repair or downgrade a deterministic pass to "needs human review". It can never turn a
fail into a pass. A wrong critic then costs a wasted iteration, never a wrong result.
Evidence: to be produced at S5/S6; recorded here in advance so the design cannot drift.
Revisit when: There is measured evidence about critic precision on this task.

## D013 - export_stage() must set defaultPrim before Export()

Status: accepted
Reason: The human's known-good WebRTC viewer (`view_usd_webrtc.py`) loads any file
by *referencing* it under a fresh prim (`GetReferences().AddReference(path)`), not
by opening it directly. USD composition resolves an unqualified reference through
the target layer's `defaultPrim`; `Stage.Export()` does not set one on its own. Our
S2 scene export (ground + box + probe, built live in Kit) never called
`SetDefaultPrim`, so referencing it resolved to nothing. The viewer's own diagnostic
made this unambiguous: "1 prims, 0 meshes, bbox size 0.0000 x 0.0000 x 0.0000,
top-level prims = []" -- and USD itself logs
"Unresolved reference prim path ... <defaultPrim>" when this happens.
The user saw only the viewer's own placeholder floor and correctly reported
"there's nothing there". `usd_author.py` (S3) was never affected: it explicitly
sets `stage.SetDefaultPrim(root)` before saving.
Alternative: Telling users to always open S2 assets directly instead of by
reference. Rejected: the referencing viewer is the user's actual known-good tool,
and a library should not require callers to route around a missing default.
Consequence: `IsaacSimRuntime.export_stage()` now sets `defaultPrim` to the given
root (default `/World`) whenever the stage does not already have one, before
calling `Export()`. Covered by `tests/test_export_defaultprim.py`, which first
reproduces the failure with pxr directly (no export_stage involved, so the bug is
proven independent of our fix) and then proves the fix. That test needs `pxr` and
is skipped under the plain system Python that runs the rest of the suite; run it
under the Isaac venv interpreter to execute it.
Evidence: `runs/20260916T101212Z_s2_open_box_normal/asset.usda` (broken, kept as
evidence) vs the regenerated run in this session's summary (fixed).
Revisit when: never expected to reopen; this is a correctness fix, not a tradeoff.

## D014 - Ground-plane visual slab is sized off the object, not the physics collider

Status: accepted
Reason: The physics collision plane can reasonably stay large (20 m), but the
*visible* slab inherited that size. Any viewer that auto-frames on world-space
bounding box then shows a 20 m grey wall next to a 0.3 m box -- which is exactly
the screenshot the user reported ("只看到一個地板而已"). `view_usd_webrtc.py`
excludes prims whose name contains "groundplane"/"floor"/"physicsscene" from its
own auto-frame, but only in its OWN scene construction; our exported floor still
dominates the bounding box for anyone who computes it differently (e.g. `pf verify`
G1 checks, or a future viewer).
Alternative: Shrinking the physics plane too. Rejected: `UsdGeomPlane` is treated
as infinite by PhysX regardless of its authored width/length, so shrinking it buys
nothing physically and only risks an edge case at extreme drop offsets.
Consequence: `add_ground_plane(..., visual_size=...)` decouples the two. S2 passes
`visual_size = max(L, W) * 4` so the visible floor stays proportionate to the box
regardless of box size (see the small/tall/thick_wall cases in S3).
Evidence: this session's regenerated renders and the fixed WebRTC report.
Revisit when: a viewer needs the physics plane's true extent for some reason.

## D015 - The exported scene carries its own PhysicsScene under the default prim

Status: accepted
Reason: Isaac authors its physics scene at `/PhysicsScene`, a sibling of `/World`.
A USD reference pulls in only the default prim's subtree, so the scene was dropped
and the referenced rigid bodies had no simulation context. Measured with a script
that loads the file exactly as the human's viewer does: zero physics scenes in the
referencing stage, and the probe unchanged at z=0.47000 after three seconds of
stepping. The user's own mug asset did not hit this because its PhysicsScene sat
inside the referenced subtree.
Alternative: Relying on the viewer's fallback, which defines `/World/PhysicsScene`
when it sees none. Measured: it does create one, and the probe still does not move,
because the bodies were already referenced in without a scene to attach to. A file
that only simulates inside its author's process is not a deliverable.
Consequence: `export_stage()` post-processes the written layer, copying the scene
under the default prim and removing the root-level original so a direct open never
sees two competing scenes. The live simulation stage is untouched.
Evidence: `tests/test_export_defaultprim.py::TestPhysicsSceneReachableThroughReference`;
the reference-load script reporting `['/World/Model/PhysicsScene']` after the fix.
Revisit when: Isaac changes where it authors the scene.

## D016 - Runs export a viewable final state, because PhysX never writes back to USD

Status: accepted
Reason: PhysX publishes results through Fabric and the tensor API; it does not
write transforms back to USD. Anything that renders from USD therefore shows a body
frozen at its authored spawn pose no matter how long physics runs. Measured in one
run: after three seconds the tensor API reported the probe at z=0.22500 while USD
still read z=0.47000. The human's viewer is launched with
`useFabricSceneDelegate=0` and `readTransformsFromFabricInRenderDelegate=0`, so it
reads USD and showed a cube hanging motionless above the box -- which is exactly
what the user reported.
Alternative: Asking the user to relaunch their viewer with fabric enabled.
Rejected: parcel-forge should not require someone to reconfigure their working tool
to see our results, and that route still only shows live motion, never the verified
end state.
Consequence: each S2 run writes `scene_final.usda` in addition to `asset.usda`.
`asset.usda` keeps the pre-simulation spawn pose (open it with `--physics` to watch
the drop); `scene_final.usda` carries the probe at the pose **measured in that run**,
taken from the last row of `trajectory.csv`. This is a record of a real result, not
a re-staged scene, and `s2_result.json` names the source explicitly. Render evidence
under `renders/` still comes from the live final state, never from this file.
Evidence: `scene_final.usda` reads z=0.22500 in USD against `asset.usda`'s 0.47000,
in the same run.
Revisit when: A USD-writeback path is enabled, which would make this redundant for
motion but not for archiving the end state.

## D017 - Finding: the S2 pass is dt-dependent, and thin plates can be tunnelled

Status: RESOLVED 2026-09-16 by enabling CCD (see resolution at the end of this entry)
Reason: While reproducing the viewer's load path, the same scene was stepped at
dt = 1/60 instead of the project's 1/240. The probe passed straight through the
5 mm bottom plate and came to rest on the world floor at z = 0.02000 instead of
inside the box at z = 0.22500. At 1/240 it lands correctly. The probe reaches
roughly 2.2 m/s before contact, which is about 3.7 cm per step at 1/60 against a
5 mm plate -- classic tunnelling.
Why this matters: every S2 "pass" so far is conditional on dt = 1/240. The profile
records that dt, so the runs are honest, but the asset is not yet robust, and
nothing in the suite would currently catch a regression here.
Consequence: recorded now rather than quietly left in place. S4 owns the fix, since
its acceptance already includes "does not fall through" and its scope covers contact
settings: it should either enable CCD for the probe, or add a dt-sweep case that
asserts the box still contains the probe at coarser timesteps, or both. Raising dt
until it passes is not an acceptable resolution.
Evidence: reproduction script output at both timesteps, quoted above.
Revisit when: S4 implements contact/CCD work; this decision then gains its result.

## D018 - Correction to D016: the human's viewer DOES write physics back to USD

Status: accepted, corrects D016
Reason: D016 claimed "PhysX never writes results back to USD" and generalised that
to the human's WebRTC viewer. The measurement behind it was real but the
generalisation was wrong. Two different code paths exist:
  * `SimulationManager.step()` (what parcel-forge uses) publishes through Fabric and
    the tensor API, and does NOT update USD. Measured: tensor 0.22500 vs USD 0.47000.
  * `omni.physx`'s `get_physx_simulation_interface().simulate()` + `fetch_results()`
    (what `view_usd_webrtc.py` uses) DOES write transforms back to USD.
The viewer therefore shows live physics correctly. The original symptom -- a probe
frozen in mid-air -- was caused solely by the missing PhysicsScene (D015), not by
any writeback issue.
Consequence: `scene_final.usda` keeps its value as an archived, directly viewable
record of the measured end state, and as a file that needs no physics at all to
display. But it is no longer justified by "the viewer cannot show physics", and the
S2 code comment claiming that has been corrected.
Evidence: `view_usd_webrtc.py` lines 327-360; the user reporting the probe had
already fallen by the time they connected.
Revisit when: never; this is a factual correction.

## D019 - Finding: the drop finishes before a human can connect

Status: open finding
Reason: The viewer runs physics on every render tick, and executes roughly 277 ticks
(2 + 200 warmup + 15 + up to 60 for the screenshot) at dt = 1/60 -- about 4.6 s of
simulated time -- before it prints READY. The probe's fall from z=0.47 to its resting
pose covers 0.245 m, which takes sqrt(2*0.245/9.81) = 0.22 s, or about 13 ticks. By
the time a human connects, the interesting part has been over for four seconds.
Consequence: a human-facing view is a different artefact from a test scene, and the
project has been conflating them. Recorded now; a `pf demo` scene tuned for watching
(probe released late, larger and higher, optionally repeating) belongs to the
human-evidence work, not to the S2 acceptance cases, whose geometry must not drift
to make a demo look better.
Evidence: `view_usd_webrtc.py` step() call sites; the user's report.
Revisit when: the demo scene is built.


### D017 resolution

Fixed by enabling continuous collision detection, on both the probe
(`PhysxRigidBodyAPI.enableCCD`) and the physics scene (`PhysxSceneAPI.enableCCD`) --
per-body CCD does nothing unless the scene enables it too.

Discrete collision samples position once per substep; CCD sweeps the volume the body
travelled through, so a 5 mm plate stops the probe regardless of how far it moved
that step.

Verified by `./scripts/pf box --dt-sweep`, which is now a permanent regression:

| dt | box-local z | verdict |
| --- | --- | --- |
| 1/60 | 0.02500 | pass |
| 1/120 | 0.02500 | pass |
| 1/240 | 0.02500 | pass |

Before the fix, 1/60 gave 0.02000 -- the probe on the world floor, having passed
through the box. All three timesteps now agree to five decimal places, so
containment is a property of the asset rather than of the solver settings.
The resolution was not "raise dt until it passes", which the original entry ruled out.
Evidence: `runs/20260916T141258Z_s2_open_box_normal_dt_sweep.md`.

## D020 - `pf view`: a human-facing viewer that plays the timeline

Status: accepted
Reason: The user could not drag the probe in their own viewer. Cause found in
`omni/physxui/scripts/input.py`: the physics grab/push input actions are registered
only on a timeline PLAY event (`use_actions(True)` under `TimelineEventType.PLAY`)
and unregistered on STOP/PAUSE. A viewer that drives physics by calling
`get_physx_simulation_interface().simulate()` directly never fires that event, so
mouse interaction can never engage however live the simulation is. This is a
property of that script, not of our asset: the probe is an ordinary dynamic body.
Alternative: Editing the user's `view_usd_webrtc.py` to add `timeline.play()`. That
file belongs to a different project which this one must not modify.
Consequence: `pf view` opens a run's scene, plays the timeline (arming interaction),
and holds the probe kinematic for a configurable period so the drop happens *after*
a human has connected -- which also addresses D019. It refuses to start when the
WebRTC ports are occupied and prints the owner's own stop command rather than
killing anything.
Its output is never acceptance evidence: only a human can report what they saw.
Evidence: `omni/physxui/scripts/input.py` lines 67-73.
Revisit when: a second viewer is needed, or the ports need to be configurable.

## D021 - Livestream is enabled by Kit argv, not by a SimulationApp config key

Status: accepted
Reason: `pf view` was written with `SimulationApp({"livestream": 2})`. That key does
not exist: `isaacsim/simulation_app.py` contains no reference to `livestream` at all,
so the option was silently ignored, no stream server ever started, and no port was
bound. The user connected to nothing and saw a grey screen -- an accurate picture of
a stream that was never running. Setting `/exts/omni.kit.livestream.app/...` through
`carb.settings` after construction is also too late; the extension reads its
configuration at startup.
The working mechanism, read from IsaacLab's `app_launcher.py` (used as an API
reference only, not as a dependency -- D001 stands): append Kit command-line
arguments to `sys.argv` **before** constructing `SimulationApp`:

```
--/exts/omni.kit.livestream.app/primaryStream/signalPort=49100
--/exts/omni.kit.livestream.app/primaryStream/streamPort=47998
--/exts/omni.kit.livestream.app/primaryStream/allowDynamicResize=false
--/exts/omni.kit.livestream.app/primaryStream/streamType=webrtc
--enable omni.kit.livestream.app
```

The port and `allowDynamicResize` settings are not optional: IsaacLab's own comment
records that without them NVST fails to bind its server socket.
Also missing and now fixed: `--enable omni.physx.ui`. Without that extension there is
no mouse grab at all, however correctly the timeline is playing -- so D020's fix was
incomplete on its own.
Consequence: a silently-ignored config key produces a failure that looks exactly like
a network problem. Anything that claims to start a service must be verified by
observing the service, not by the absence of an error. `pf view` is now checked by
confirming the port is bound and READY is logged.
Evidence: `ss -lnt` showing `0.0.0.0:49100 LISTEN`, and `runs/viewer.log` reporting
`READY - connect WebRTC to 140.113.203.85:49100`.
Revisit when: the ports need to be configurable per session.

## D022 - A tool that holds a resource must be able to release it

Status: accepted
Reason: `pf view` refused to start when the WebRTC ports were busy and told the user
to run the *handoff project's* stop script. But the process holding the ports was a
parcel-forge viewer that this agent had started in the background. That script writes
and reads its own PID file, so it reported "no PID file" and stopped nothing. The
user ran it four times in a row against a port that parcel-forge itself was holding.
Two separate mistakes: leaving a long-running process behind without telling the user
how to stop it, and printing a fixed remedy that assumed the blocker was someone
else's.
Consequence:
  * `pf view` now identifies the actual port holder (pid and command line) via
    `ss -lntp` and `/proc/<pid>/cmdline`, and branches on whether it is ours.
  * Ours: `./scripts/pf view --stop`, or `--replace` to take over in one step.
    Stopping our own process needs a SIGKILL fallback, since Kit routinely ignores
    SIGTERM and would otherwise keep the port.
  * Not ours: it still refuses and names the owning process, so the user can decide.
    D003's rule stands -- parcel-forge never stops a process it did not start.
Evidence: the `--stop`/`--replace` cycle exercised end to end; the message now prints
the owning pid.
Revisit when: more than one parcel-forge service can hold a port.

## D023 - Hold the probe with gravity, not by making it kinematic

Status: accepted
Reason: `pf view` originally held the probe by setting `kinematicEnabled = true`.
PhysX rejects that combination with our D017 fix:
"PxRigidBody::setRigidBodyFlag(): kinematic bodies with CCD enabled are not
supported! CCD will be ignored." CCD is precisely what stops the probe tunnelling
through the 5 mm bottom plate, so a hold that silently discards it risks the viewer
showing behaviour the test suite has ruled out. Whether CCD is restored when the
kinematic flag is cleared is not something to assume when the check is this cheap.
Alternative: Keeping kinematic and re-asserting CCD on release. Rejected: it depends
on undocumented ordering, and a gravity toggle has none of that risk.
Consequence: the hold now sets `PhysxRigidBodyAPI.disableGravity`. The body stays
dynamic throughout, so CCD is never disabled, and a bonus: a held probe can still be
pushed around with the mouse before it is allowed to fall.
Evidence: the PhysX error in `runs/viewer.log` before the change; absent after.
Revisit when: a hold is needed for a body that should also ignore contacts.

## D024 - The Kit experience file decides whether there is any editor UI

Status: accepted
Reason: The user asked why `pf view` showed a bare viewport with none of the windows
their previous viewer had. Cause: `SimulationApp` takes an `experience` argument and,
when it is empty, resolves to `isaacsim.exp.base.python.kit` -- a minimal app that
renders a viewport and nothing else. It is not a livestream limitation and not
something `headless` controls.
Isaac Sim ships `isaacsim.exp.full.streaming.kit`, described in its own package
metadata as "Headless Isaac Sim with Livestream using WebRTC": it depends on
`isaacsim.exp.full` and sets `app.window.hideUi = false`.
Consequence: `pf view --ui` loads that experience, giving the stage tree, property
panel, toolbar and the PhysX debug visualisation (collider wireframes, which are
genuinely useful for confirming that the box walls are where the geometry says).
Without `--ui` the minimal experience is kept: it starts faster and is enough when
only the result matters.
Evidence: 3 editor UI extensions loaded and `hideUi = false` in the .kit file;
verified by a run reaching READY with the port bound.
Revisit when: a purpose-built layout is wanted rather than the stock editor.

## D025 - `hide_ui=False` is required on top of the full experience

Status: accepted, completes D024
Reason: Selecting `isaacsim.exp.full.streaming.kit` was not enough: the stream still
showed a bare viewport. `SimulationApp`'s own documentation explains why --
"`hide_ui` (bool): Hide UI when running to improve performance, **when headless is
set to true, the UI is hidden, set to false to override this behavior when live
streaming**". We pass `headless=True` (there is no display), so the UI was hidden
regardless of which experience was loaded.
Consequence: `pf view --ui` sets `hide_ui: False` in the launch config as well as
selecting the experience. Verified by the resulting Kit command line containing
`--/app/window/hideUi=False`, and by `omni.kit.window.stage`, `window.property`,
`window.toolbar` and `content_browser` all starting.
Lesson worth keeping: two independent switches had to agree before anything visible
changed, and neither reported a problem on its own. "I set the option" is not
evidence; "the service shows the effect" is.
Revisit when: never expected; this is how the API is documented to work.

## D026 - The evidence camera frames the subject, not the scene furniture

Status: accepted
Reason: The viewer opened with the camera metres away from a 30 cm box. The framing
code took the bounding box of `/World`, which includes the ground slab -- several
times wider than the box by design -- so the computed radius was the floor's, not
the subject's.
Consequence: framing now unions only the children of `/World` whose names do not
look like infrastructure (ground plane, floor, light, physics scene, render, camera),
and logs what it framed on: `framing on ['Box', 'Probe'], extent 0.300 m`. The
user's own viewer solved this the same way, with a name-marker exclusion list; the
approach is borrowed deliberately.
Revisit when: an asset legitimately contains a prim whose name matches a marker.

## D027 - Finding: the probe is very light, so mouse drag throws it

Status: open finding (behaviour is correct; the parameter choice is the question)
Reason: The user observed that a light drag sends the probe flying, and asked whether
gravity was wrong. It is not. Checked against run evidence:
  * gravity reads back as (0, 0, -1) x 9.8100004196167 m/s^2;
  * S1's free-fall check matches the analytic drop to 2.04 mm at t = 0.1 s, which is
    exactly the expected semi-implicit Euler overshoot;
  * the probe comes to rest at precisely half its edge length above the floor.
The cause is the mass. The probe is a 4 cm cube at 0.05 kg, so its density is
781 kg/m^3 -- lighter than water -- and it weighs **0.49 N**. Omniverse's mouse
interaction applies a force that does not scale with mass, so a drag of order 1 N
gives a = F/m = 20 m/s^2, about 2 g. A light object flying under that force is
correct physics, not a bug.
Consequence: recorded rather than "fixed", because nothing is broken. `probe.mass_kg`
is a case-file parameter whose provenance is already `uncalibrated_assumption`, and
raising it is a one-line change per case. For a 4 cm cube: ~0.058 kg is
polypropylene, ~0.064 kg is water, ~0.17 kg is aluminium, ~0.50 kg is steel.
What this does flag: the project has never justified 0.05 kg against anything. It is
a number chosen to be convenient. Any demo intended to look plausible should pick a
mass from a stated material, and say which.
Revisit when: a case needs a defensible probe mass, or a demo profile is built.

## D028 - Methodology review: inertia feasibility and uncertainty scope

Status: open finding; implementation plan pending user confirmation.
Evidence: `runs/20260916T151106Z_methodology_review/inertia_counterexamples.json`.
The current check accepts principal moments (4,1,1) after rotation, and rejects a
valid small tensor via an absolute determinant threshold. Prior confidence in full
pseudo-inertia enforcement is superseded by this counterexample. Scalable Real2Sim
identification error is not an authored-value transport tolerance. Proposed repair
is a separate validator-correctness task per handbook section 14; no asset verdicts
or profiles were changed. See review_plan.md in the same run for sources and gates.

## D029 - Incremental R-stage company reports

Status: superseded by D030
Reason: The S0-S7 roadmap is a technical gate and can contain too much work for one
company status update. The user needs small, evidence-backed increments that show
work accumulating over time.
Consequence: `config/progress_stages.json` defines immutable reporting slices R00,
R01, ... independently of the technical stage. `pf report` writes a new append-only
run with Markdown, machine-readable evidence audits, hashes, PNG dimensions and
trajectory SVGs. A stage may be `in_progress`; file existence never upgrades it.
Historical runs without continuous render frames explicitly report video as
`not_available`. Future motion-dependent stages capture video during simulation.
Evidence: `runs/20260916T152811Z_progress_report_R03/` and
`runs/20260916T152812Z_progress_report_all/`.
Revisit when: company reporting requires a fixed PPTX/PDF template.

## D030 - Two plain report folders

Status: accepted, supersedes D029
Reason: Company reporting does not need a CLI, registry, report schema or automated
chart generator. Two distinct questions must remain clear: how far the workflow
itself has been built, and how far one actual workflow execution has progressed.
Consequence: `reports/development/` holds chronological workflow-construction
reports. `reports/execution/` holds per-case or per-batch step tables that may begin
with later steps as `not_run` and be updated as the run proceeds. Both are ordinary
Markdown. Original machine evidence remains under append-only `runs/`; reports link
to it. Historical PNGs may be linked, but missing historical video stays
`not_available`.
Evidence: `reports/development/2026-09-16_workflow_build.md`,
`reports/execution/2026-09-16_open_box_baseline.md`, and `runs/20260916T153821Z_report_folders/`.
Revisit when: the company provides a mandatory document or slide template.

## D031 - Numerical transport is not physical identification

Status: accepted
Scalable Real2Sim errors concern real-object identification. S4 compares authored
USD values with PhysX values, so it uses tight transport tolerances. Shell mass and
distribution remain estimated. Evidence: runs/20260916T155652Z_s4_mass_readback/.

## D032 - Wall blocking uses the whole trajectory

Status: accepted
Final pose can hide a prior wall crossing. Each direction records maximum signed
centre coordinate; it must reach within 10 mm and overshoot by no more than 2 mm.
The pure rule has boundary, tunnel and never-reached tests.
Evidence: runs/20260916T161010Z_s4_sidewall_recovery/.

## D033 - Save physics before optional rendering

Status: accepted
The first wall run completed all trajectories and scene export, then Kit exited -11
during rendering. Runtime now checkpoints physics before rendering; physics and
render keep independent statuses. Old runs remain unchanged.
Evidence: runs/20260916T160621Z_s4_sidewall/ and
runs/20260916T161010Z_s4_sidewall_recovery/.

## D034 - Contact claims distinguish authored, composed and runtime behavior

Status: accepted
Explicitly author contact/rest offset and material friction/restitution on all
colliders; save pre/post-play composed USD readback and binding. These are estimated
engineering values. Do not label them an internal PhysX coefficient readback.
Evidence: runs/20260916T163041Z_s4_sidewall/ and runs/20260917T000241Z_s4_placement_grid/.

## D035 - CCD attribute does not establish effective CCD

Status: accepted; supersedes D017 causal attribution, preserves measured outcomes.
The local GPU pipeline logs that suppress readback disables CCD. Record effective
status disabled_by_runtime_warning even when the scene attribute is true. Successful
containment is empirical at the tested settings; it does not prove CCD is active.
Evidence: runs/20260916T163330Z_s4_dynamic_drop/logs/isaac_runtime.log.

## D036 - Human verification uses measured final scenes and separate records

Status: accepted
User needs commands for each small milestone. Retain S1 final tensor pose in USD,
add optional physics-only mode, checkpoint physics before rendering and classify
external crashes as insufficient evidence. Default rendering consumes the original
live stage before writing final pose for export. This does not establish a root
cause for the preserved crash. Final-scene viewing is not trajectory replay;
viewer starts separate physics with its own dt. Human confirmations stay separate
from deterministic and renderer verdicts.
Evidence: runs/20260917T004549Z_s1_smoke/ and runs/20260917T004937Z_s1_smoke/.

## D037 - Adopt upstream workflow machinery, retain ITRI acceptance

Status: accepted direction; integration unverified.
User approved planning migration to NVIDIA USD Content Agents. Supersedes custom
S5 repair-loop implementation route, not task acceptance or D012. Pin full upstream
SHA and isolate its environment. First reproduce its no-VLM validation example,
then bridge normal/missing-bottom evidence, exact recordings and bounded agent
repair. BYOR numeric tuning is distinct from geometry/spec repair.
Never map a fault regression pass to an asset acceptance pass. Generic USD sanity
can pass while task containment fails. Preserve both source reports and require
ITRI gates. Old S0–S4 artifacts remain immutable historical baselines.
Plan: docs/UPSTREAM_ADOPTION_PLAN.md; current task S5A_upstream_baseline.md.

## D038 - Isolate the pinned validation baseline and archive real test videos later

Status: accepted; S5-A verified, video implementation pending S5-C.
Pin upstream 0.6.0 a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa, keep its source
clean and all new packages in .venvs/usd-content-agents. Direct fixed-pipeline
Validation Agent is explicitly selected for this baseline, not a silent agentic
fallback. Fixture approval is not new physics or a live model judgment.
User requested clickable test-process videos. Retain exact rollout and PNG evidence,
then encode MP4 with installed ffmpeg as a human-review attachment. Never substitute
it for unsupported upstream judge input or resimulate a purported recording.
Evidence: runs/20260917T010638Z_s5a_upstream_setup/.

## D039 - Keep upstream sanity and ITRI task acceptance as distinct gates

Status: accepted, verified.
Pinned upstream physics_sane passes both normal and missing-bottom USD. Its sanity
scope does not prove containment. The thin adapter freezes hashes, checks original
input/asset hashes and finite complete CSV, recomputes existing local-frame outcome
and requires inside irrespective of fault-regression expectation. It does not invent
a model refine approval. Source CSV hash protection starts at first bridge binding.
Evidence: runs/20260917T012612Z_s5b_completion/bridge_suite.json.

## D040 - Render frozen measured animation with zero timeline increment

Status: verified for S2 single-probe recordings.
Use actual CSV time/pose samples; no new physics to manufacture motion. Retain
NVIDIA exact-rollout USD/PNG path and attempt its pinned renderer. OVRTX isolated
runtime absent with auto provisioning disabled; use existing Isaac Replicator
step(delta_time=0, wait_for_render=True), checking timeline drift. PhysicsScene
removed, bodies disabled. MP4/ffprobe are human delivery, not upstream judge
approval. 900 samples per case checked exactly; 450 frames at 30 FPS, 0.25x.
Only recorded interval/single S2 probe supported; human viewing not_tested.
Failed empty-RGB attempts retained. Evidence in S5-C reports and suite.json.

## D041 - Generate videos on demand in an independent background process

User approved a background script for recording. Numeric evidence remains the
routine development output. Explicit ./scripts/pf-video-background --run <id>
launches one detached worker and archives request/PID/log/final result under a
fresh run; no service, scheduler or new dependency. The same existing pf video
checks provenance, VRAM, rendering and MP4. GPU rendering still consumes resources;
this frees developer waiting time, not guaranteed render speed. Keep stage videos
and useful before/after comparisons; do not render every test. Never stop shared
processes. Completion is verified separately from successful job launch.

## D042 - Narrow proposal gate before official agent repair wiring

Local repair_proposal/1 supports only one /geometry/fault change from sealed_lid
or missing_bottom to none. Everything else, especially probe/expected_outcome/
profiles, is forbidden through this interface. Preserve original source and
proposal, validate schema, emit a new candidate only. Hand-authored proposals
verified before/after with measured task gates; not a live model or official
checkpoint test. Legacy expected_outcome remains fault-regression metadata;
repaired candidate can fail that regression while passing task containment.
Actor filesystem sandbox and official checkpoint/resume remain pending S5-D.
Evidence: runs/20260917T015901Z_s5d_progress/repair_suite.json.

## D043 - Use official focused operation contracts and a limited write boundary

Status: focused validation and content-write probes verified; full actor pending.
Install official CLI dependency graph only in isolated upstream venv, keep pinned
source clean and shared Isaac unchanged. Use explicit outer-selected
prepare/check/finalize for physics_sane; AND with existing ITRI CSV gate. Generic
sanity cannot override task failure. Official checkpoint fresh-process load is
verified, interrupted workflow resume is not. Bubblewrap namespaces unavailable;
Landlock ABI 6 content mutation rights tested with controlled fixtures. The
boundary does not provide read/network/process/metadata isolation or full FD
protection, so do not call it a complete actor sandbox. No untrusted model shell
launched. Source: Linux kernel Landlock documentation, local syscall headers and
pinned official CLI. Evidence: S5-D focused workflow report and completion suite.

## D044 - Replace ambiguous repair v1 with source-bound v2 and receipt budget

B audit identified incompatible same-name contracts and permissive probe paths.
Active v2 permits one fault removal only; v1 rejects all and historical content
is archived in 025429Z_bc_integration. Trusted controller verifies frozen source
and hash, reserves three append-only receipts per original source under flock,
including rejected submissions. v1 historical tool proposals do not retroactively
consume v2 budget. Receipt cannot be reset by actor-supplied attempt=1. Candidate
provenance chain stays outside strict case schema. Content linkage to historical
measured runs is not a new simulation or causal execution claim. C duplicate
launch exit 3 is retained; startup flock and suffix scan fix concurrent/suffixed
jobs. Fake process tests are not render acceptance.

## D045 - Respect pinned upstream's actual spec-repair integration limit

A source audit: pinned validation registry accepts its four existing templates,
not arbitrary ITRI checks. Native USD topology/physics repair is distinct from
JSON box-spec repair. Keep outer spec proposals, controller gate and ITRI task
acceptance external; reuse official focused validation and checkpoint contracts
where supported. No fictitious generic plug-in, no replacement of an existing
validator to gain a pass. Node/npm absent does not block current deterministic
physics_sane flow. Child-runner/model integration and full actor boundary remain
pending, as does interrupted resume. Existing S5-D descriptions are amended,
not silently marked completed. Source: upstream_wiring_audit.md and pinned code.

## D046 - Qualify resume by template and preserve failed validation after recovery

Measured: pinned run_validation_workflow Wave 2 accepts visual templates only;
physics_sane checkpoint generated by focused flow does not imply resume support.
Do not upgrade or patch upstream to hide this limitation. Trusted render_valid
interrupt after RUNNING claim, identity-change refusal, live-claim refusal, and
explicit recovery after own process exit tested. Unavailable OVRTX final fail and
CLI exit 1 are preserved while state completion reaches attempts=2. Diagnostic
pass is not asset/render/physics/model recovery pass. No mock render approval.
Fresh v2 missing-bottom candidate actually rerun under unchanged source profile;
new chain and focused task gates pass, original fault expectation remains fail.
Progress ~70% is an equal-stage planning proxy, not measured effort or material
accuracy. See resume_and_progress report and completion suite.

## D047 - Restart unsupported physics stages without pretending checkpoint resume

Accepted candidate may be reused without allocating another proposal receipt; failed
physics gets a complete new run under the original frozen profile. Link/focused checks
get fresh evidence directories. physics_sane is re-prepared/checked/finalized because
D046 measured resume unsupported. Visual claim recovery requires the owning process
to have exited and preserves final failure. This is a documented manual policy, not
an automatic restart controller. See docs/REPAIR_RESTART_POLICY.md.

## D048 - Use JSON-only file exchange before provisioning a model runner

No configured model endpoint or callable model tool measured. Prepare freezes source
evidence and prompt with advisory next attempt under budget lock, never reserves it.
Check retains raw answer, rejects duplicate keys/nonfinite JSON/out-of-scope changes
and emits only ready_for_controller_submission. Controller alone reserves attempts
and accepts candidate; stale attempts still rejected. File exchange cannot attest
model identity or execution, so offline fixtures never count as model success.
No shell runner, installation or fictitious upstream hook added.

## D049 - Distinguish keyboard showcase, geometry source generation and handoff

README keyboard training image is not a copy-paste reproducible generation recipe.
Official geometry run consumes source/manifest; asset run requires source and explicitly
routes text/image authoring to geometry-agent. Use the existing outer coding agent,
configured authoring provider and typed source, without inventing another scheduler.
Existing-box official dry-run keeps required rendering defaults, is plan success only,
not generation/quality success. ITRI frozen probe/profile/task gate remains external.
Sources: pinned README, connectors README and saved CLI help.

## D050 - Bounded trusted executor with per-stage immutable completion records

Reuses accepted v2 proposal, snapshots and re-verifies receipt/patch/source hashes,
checks selected GPU resources, invokes existing box generator/physics, recomputes
link/task then runs official focused validation. Failure stops chain. Stage 01–05
records and final result do not pretend checkpoint resume. Original regression
exit 2 cannot alone determine repair success; measured task and official gates
required. No model shell, external generator, scheduler or auto video.

## D051 - Codex authored four-flap proxy with correct USD units and explicit failures

User authorizes current Codex modeling, independent of absent external geometry service.
Installed Isaac 6 API, per-degree USD gain conversion, dimensionless joint friction,
viscoplastic viscosity and accumulated-plastic softening documented. Finite-thickness
flap-tip clearance repairs geometric startup jam with collisions enabled, not by
relaxing gates. Fixed low-control experiment obstructs minor lids; full result remains
fail. Force-drive offset is a virtual torque actuator, not measured robot contact.
Rigid proxy cannot claim orthotropic plate bending; standalone USD needs Python controller
for plastic updates. See prototype report/source references and preserved failures.


## D052 - Independent carton diagnostics preserve old mixed-load failure

Closed low-load major blocks minor lids; do not switch low-control joint to pass old gates.
Separate opening-order (all-high, major-first then minor) and crease coupon (majors held; low/high minor)
with declared checks, existing failure untouched. Add explicit cyclic opening/closing profile and lower-yield bound.
Finite-thickness side kerf is generator geometry, not collision disablement. Avoid duplicate unchanged
position-target writes; observe settling after drives stop changing. Sleep/contact can affect stopped angles,
so do not claim force-balanced material calibration. Real rigid panels cannot prove MD/CD bending.
Runtime progress.jsonl and development reports are separate. Native41 rules aren't material certification.

## D053 - Root defaultPrim and effort-unit crease friction on Isaac6

Official DefaultPrimChecker rejected nested /World/Carton. Generator now defaults /World (root),
old failure kept and fresh official negative proves detection. No rule omitted or tolerance changed.
Local Isaac6 Articulation API has PhysxJointAxisAPI angular static/dynamic friction efforts; explicit
.005Nm variant avoids treating legacy dimensionless coefficient as torque and is verified via tensor readback.
Legacy coefficient profile remains available unchanged; effort variant sets coefficient0 to avoid mixed models.
All guessed parameters remain uncalibrated_assumption, including fatigue law. Geometry author, validation,
stateful controller and measured replay isolated; replay disables physics only in derived recording, not asset repair.
No official child/provider or IsaacLab integration claimed. See proxy milestone report with sources/evidence.


## D054 - Separate measured replay and user-driven live carton interaction

recording.usda disables physics intentionally and cannot respond to force. Manual Script Editor
loader opens active asset.usda and retains a LiveCarton instance, registering only own PREstep
and STOP callbacks. Installed Isaac6 callback(dt,context) and Articulation tensor methods verified
in headless run; UI construction separate from native mouse/WebRTC verification. NVIDIA documented
mouseInteractionEnabled/mouseGrab/forceGrab plus Shift-left-click used; no UI success claimed without human.
Torque pulses use force-drive reference offset, not pose edits. Duplicate constant targets avoided.
Stop resets own plastic history; pause retains it. Stage switch fails closed; close removes only own
callbacks/window. Fixed box/rigid panels cannot crumple/tear. All material estimates persist.
Manual loader doesn't autoplay or start extra viewer; private headless test strong-references source
USD Stage to avoid weak-layer lifetime fatal. See live interaction report sources and append-only evidence.


## D055 — Directional segmented strips with literature provenance

Use separate panel bending joints, not directional crease springs, for MD/CD proxy. Cell k=D*b/h derives from bending energy; clamp half-cell doubles k. Published130TL board D/mass/thickness do not calibrate our crease or assert matching our box. New16-DOF topology profile preserves rigid four-DOF gate. Existing active joint drive radians-to-degrees convention retained. Zero-gravity coupon isolates material proxy; carton uses9.81. Beam loading is virtual end couple via force-drive offset, not pose forcing. Model covers one-dimensional bending only, with numerical damping and explicit material orientation assumptions. New callback owns only its events and supports strict declared extra joints; baseline exact four-DOF behavior retained. Exception must force fail even after a subtest passed; old121636 misclassification preserved and explicitly superseded. Private runtime scene reused without invalidating SimulationManager PhysicsScene; no shared viewer reset.


## D056 — Passive material response, separate external-force apparatus

User rejects open/close state commands. New interaction_mode external_forces_only rejects legacy drive-offset actuator. UI open/close buttons removed. Constitutive callback computes only plastic references; optional ForceProbe applies physical outer-edge forces using RigidPrim and owns separate callbacks. Robot integration attaches material only. New estimated panel plasticity preserves literature stiffness, derives Y from assumed yield curvature2/m and relaxationtime.05s; no material calibration claimed; ±30degree limits affect large-damage equilibrium. Original elastic coupon and legacy gate remain unchanged. Collision-based kinematic spherical fingertip test measures contact force and independent motion without carton commands; uses version-matched explicit stage ID and kinematic targets, not teleports. User-owned viewer not reset.

## D057 — Mouse UI activation rejected; diagnose before claiming interaction

Readonly headless diagnostic finds physics mouse UI extensions disabled and pickingForce1.0; does not prove viewer identical. Automatic approval rejected enabling installed UI as Isaac reconfiguration forbidden by AGENTS. No activation code executed, installed environments unchanged. Explicit user exception required before any activation; proposed scope only already-installed110.1.13 UI in current app, no install/upgrade/configfile/viewer restart. New passive loader reports readonly state; native WebRTC remains not_tested despite external-force/contact success.


## D058 — Own-view disposal and force-mode test apparatus

UnexpectedStage refcount warning does not establish physics cause. Old controller/probe held own USD references after deregistering top-level callbacks. Installed Isaac6 Prim registers strong internal callbacks; explicitly detach only own views using version-matched _deregister_callbacks, clear own weak timeline subscription and prim refs, then clear stage/joint/view fields. Never clear global manager callbacks or reset others. Loader cleans legacy own fields before opening next stage; repeated force UI reuses same instance; reload cached owned tool modules. External force signs mean normal pull/press, finite strike pulses replace continuous force and end; no carton open/close state. UI10N button construction separate from executed-1N pulse and human click verification. Mouse extension activation remains rejected/pending user exception.


## D059 — Preflight and bind own package search before asynchronous stage replacement

Long-lived Kit may cache package path or negative imports; actual viewer cause unknown despite local lifecycle file existing. Manual entry checks file visibility and points only parcel_forge namespace search/spec at repository src, invalidates import caches before legacy cleanup. Do not clear all sys.modules or install/reconfigure shared runtime. Own task done callback retrieves errors. Real private Kit executes actual entry with deliberately stale package path, physical force and second load verified; not native viewer mouse proof.


## D060 — Settledness measured from angle, legacy mixed-load scenario retired as a spec error

User authorised both repairs on 2026-09-17 after seeing the evidence; neither is a threshold relaxation.

Settledness: the articulation DOF velocity readback holds a stale nonzero value while a flap rests against a sustained contact. In 20260917T105836Z_ext1_carton HingeMajorYP reported 0.2651888430118561 rad/s for the final 7.2 s while its angle stayed bit-identical at 0.2819564938545227 rad; the offline replay in 20260917T130752Z_ext1_settle_spec_delivery measures a trailing 1 s angle span of exactly 0.0 rad. The fresh run 20260917T130538Z_ext1_carton reproduced the artefact independently (HingeMinorXN 0.339 rad/s readback, 0.0021 rad trailing span). The gate is now the trailing 1 s angle span divided by the window, with the same 0.02 rad/s tolerance as before, so the mean-rate criterion is unchanged; the velocity readback is still recorded in settle_metrics and reported as velocity_readback_settled, never hidden.

Legacy mixed-load: that scenario holds one major flap closed under low load while requiring both minor flaps to open plastically. On an RSC the minors fold under the majors, so the closed major physically blocks them and no torque satisfies the gate. Measured: 0.08 N.m moved the minors 0.57 deg there, and 100 deg in the opening-order scenario once the majors were open. The scenario is therefore retired as a specification error, not relaxed: it stays runnable, its checks are still computed and reported, its status is the new terminal value superseded which never becomes pass, and pf-carton still exits nonzero for it. All old run directories are untouched. The low/high load contrast it was meant to test is carried by crease-coupon, which compares two minor flaps with nothing above them. pf-carton now defaults to opening-order. No collision was disabled and no material parameter changed; all values remain uncalibrated_assumption.


## D061 — The flap felt wrong for three measurable reasons, and the panel was not integrable

User reported: the flap could not be pulled open, nothing he did left a permanent fold, the springback was far too strong, and the panel opened as separate flapping strips. New offline module `carton_feel.py` turns a config into quantities a hand can feel, and it explains all four on the asset the user was loading (20260917T123830Z, MajorYN):

- crease yield angle Y/k = 0.03/0.04 = 43 deg, so nothing creased until the flap was already most of the way open, and the springback after creasing was the same 43 deg;
- the viscoplastic flow rate depends only on the angle, and the angle is capped by the 100 deg joint limit, so the maximum plastic rate was 0.123 rad/s no matter how hard the user pulled, and creasing 45 deg required holding the flap for 6.4 s;
- the residual holding torque equalled the yield torque, 5.35x the flap's own weight torque, so a creased flap could never droop;
- the segmented panel drive had omega*dt = 24.9 against an integrable limit near 0.3, i.e. 6900x the stiffness this timestep can carry, which is why the strips buzzed and flung rather than holding the panel flat.

Repairs. `crease_model.advance` now accepts plastic_viscosity 0, which is exactly the rate-independent return map its backward-Euler form already contained, so a harder pull creases further in the same step. Crease gains are no longer typed in: `derive_carton_creases` computes them from two things a person can check on a real box, the springback angle and whether a creased flap carries its own weight, and scales stiffness and yield with crease length so every flap springs back by the same angle. The interactive asset uses rigid panels, since the board is 530x stiffer than its creases and a segmented strip of it is not integrable here; `author_segmented_carton` now refuses to author an unstable strip unless the caller passes panel_stability_policy='record', which the two legacy strip modules do so their old evidence stays reproducible.

Measured on the new asset, run 20260917T132321Z_ext1_carton_pull: 0.16 N at the tip starts a major flap opening, 0.30 N reaches 60 deg, releasing at 79.4 deg leaves it at 73.8 deg with 5.6 deg springback, a 1 N pull lasting 0.4 s leaves a permanent 98 deg fold, and a 0.05 N pull from the creased rest angle deflects the flap 3 deg and returns it with the plastic reference bit-identical. All gains remain uncalibrated_assumption; the targets are stated so a real force-angle trace can replace them.


## D062 — The drag was weak, not the crease stiff: picking force, lever arm and joint drag

User reported the mouse drag only nudges the flap. Read the installed omni.physx 110.1.13: the drag force scale is `/physics/pickingForce`, read as 1.0 in the user's application, and NVIDIA's own KaplaArenaDemo raises it to 10 to move stacked blocks. The installed package documents no newtons-per-unit for it, and there is no scriptable grab, so the delivered force cannot be measured headlessly and only the user can confirm the drag.

What can be measured is the force the asset demands, and it is small. A closed major flap must overcome its crease yield plus its own weight, 0.01401 N.m, which is 0.141 N at the outer edge, matching the 0.16 N the ramp measured in 0.02 N steps. The lever arm is the trap: grabbing halfway up the flap needs twice that, a quarter of the way up four times. Bracketed in simulation on MinorXN at the half-way point, 0.7x the predicted force moved it 1.6 deg and 1.3x opened it to 49.7 deg, so the prediction holds and a drag that lands near the crease is simply under-levered.

Three answers, none of which soften the cardboard: grab near the outer edge; `mouse_mode('joint')` drags with a constraint instead of a force and so does not depend on the picking scale at all, and is now the mode the UI selects on load; `grab_strength(value)` reads and sets /physics/pickingForce with the previous value printed for restoring. That is a setting in the running application, in the same class as the mouse settings this controller already sets, not an install, upgrade or restart, and it is only applied when called. ForceProbe now takes a grab fraction so a grab point part-way up the flap can be tested. The crease gains from D061 are unchanged: 0.141 N at the edge is not a stiff flap, and whether it matches real board is still not_tested.


## D063 — The drag has four gates before it reaches PhysX, and picking force is the last of them

pickingForce 1000 changed nothing for the user, which rules out force magnitude. Read from the installed omni.physx.ui 110.1.13: a viewport drag reaches physics only through `PhysxUIViewportOverlays.on_mouse_shift_drag_start`, which returns early unless (1) that extension is running and owns a viewport overlay, (2) the timeline is playing, (3) Shift is held for the whole drag, or `_mouse_interaction_state` is ENABLED, and (4) no other gesture or hover owns the cursor, which a selection gizmo does. Only then does it call `get_physx_interface().update_interaction(ray, event)`, and only then does the picking force matter.

That call is scriptable, so it was driven headlessly. With omni.physx.ui disabled, as it is in our standalone apps, it moved nothing at all: no POINT_GRABBED event and a plain resting control cube displaced 2e-8 m with every interaction setting on. The test therefore reports `blocked`, not `fail`, and writes blocked.json: with no interaction subsystem loaded there is nothing to exercise, and it proves nothing about the user's viewer where the extension may be enabled. One observation stays unattributed and is recorded as such: at pickingForce 1000 MajorYP spiked to 100 degrees with no grab event.

`carton_mouse_diagnostic.diagnose` now reports all four gates read-only, including whether `get_physicsui_instance()` exists, and names the blockers in plain words; the editor entry prints it on load. `LiveCarton.mouse_no_shift()` calls the extension's own `mouse_interaction_override_toggle(ENABLED)` so a plain left-drag works, and does nothing when the extension is absent. Nothing is enabled, installed or restarted; if the user's diagnosis reports omni.physx.ui disabled, enabling it is the exception that was rejected before and still needs their explicit approval. The verified way to load a flap remains the measured force tool.


## D064 — Push works, drag does not, and a pushed-shut flap now stays shut

Two reports, two separate answers.

Push versus drag. The installed defaults are asymmetric: `/physics/mousePush` is 1000 while `/physics/pickingForce` is 1.0, so a click-push carries a thousand times the scale of a grab at its default. A push is also a click, and a click never competes with the selection gizmo, while a drag does: `on_mouse_shift_drag_start` returns early when `get_active_gesture() or get_active_hover()` is set. That the user's push works proves omni.physx.ui is running in their viewer, so gate 1 of D063 is passed there and the remaining suspects are the gizmo owning the drag gesture and Shift.

Springback. The user's rule is the right one and is what the model encodes: small folds recover, folds past yield stay. Measured on the current asset in 20260917T140926Z_ext1_carton_pull with every other flap shut, a flap creased open to 96.9 deg and then pushed closed reaches -0.34 deg, is released, and stays at -0.34 deg: springback 0.00002 deg, plastic reference reset to 2.08 deg. It does not spring open. The first attempt at this measurement was contaminated and is kept: with all four flaps standing open the pressed major jammed at 85.5 deg against the raised minors after 11 deg of travel, which is interference, not recovery, and the two checks it failed were the test's fault. The sequence now presses while the others are shut and re-opens the major before the minor phases, because on an RSC a shut major traps the minors.

Since the asset measured here cannot do what the user describes, the likely explanation is that the viewer still holds the older segmented asset, whose springback is 43.0 deg against 4.0 deg for the rigid-panel one. LiveCarton now prints the loaded panel model, the springback angle and the edge force on attach, and warns when the springback exceeds 15 deg, so which asset is loaded is visible without reading a config file.


## D065 — The resident-stage warning is not reproducible here, and is recorded as unexplained

The user's viewer warned that the outgoing stage had a reference count of 2 while being closed, naming the previous asset, which places it at the moment the entry swaps assets. The editor loader test now performs that exact swap, running the real entry against one asset and then against a different one, and scans the captured Kit log for the warning. It does not appear: the swap completes, the previous controller's stage is None, and no warning is logged. A control run with the added gc.collect() removed produced no warning either, so that collection is an untested precaution and is labelled as one in the code, not a demonstrated fix.

What is left is a GUI-only difference we cannot reproduce headlessly: a selected prim of the outgoing stage is held by the selection and by the property window, neither of which exists in a private Kit. The entry now clears its own selection before opening the next stage, which is reversible with a click and also removes the gizmo that swallows the physics drag gesture in D064. This is a plausible cause treated as plausible, not a fix with evidence behind it. The warning names cleanup, not failure: in the swap test everything after the swap worked, so it does not explain anything the user reported about pulling or pushing flaps.


## D066 — The 100 degree stop was arbitrary, and the box was nailed to the world

Two limits the user ran into, both authored rather than physical.

The flap stop. `author_carton` clamped every crease to -5..100 degrees, so a flap jammed just past vertical and the carton could never be opened out. A real RSC flap folds right back against the outside of the wall, and the crease is authored on that outer face, so 180 degrees lays the flap flat on it with no interpenetration. The limits are now config, and the asset uses -5..179, the last degree left out to avoid the degenerate flat pose. Measured in 20260917T143848Z_ext1_carton_pull: a major flap folds to 179.0 degrees, is released, and stays at 179.0 with a plastic reference of 176.5.

The body. The base carried a FixedJoint to the world, which is what the flap experiments wanted and is wrong for a robot cell. `base_mode` is now fixed or free; free drops that joint and stands the carton on a ground plate. The base mass also stopped being a typed-in 0.2 kg and is now the board's areal mass over the bottom and four walls, 0.0846 kg. Measured free in 20260917T143819Z_ext1_carton_pull: a ramped sideways force breaks the box away at 0.7 N, which implies a friction coefficient of 0.84, and that is the simulator's default material, not authored or measured; pulling a flap with 0.25 N moves the box 2.3e-8 m. Two guessed shoves were discarded first and are recorded: 0.5 N did not move it at all and 20 N threw it 33 m, which is why the threshold is now ramped like the flap opening force.

The editor loader test pulled a flap with 2 N, which is 2.4 times the free-standing box's own weight and threw the whole carton, opening all four flaps. It now uses the measured 0.30 N and additionally asserts the box does not move while one flap is pulled. Declaring a physics material for the board and the ground, so the friction coefficient is ours rather than the simulator's default, is the next thing to do and is not done.


## D067 — 270 degrees, not 180: the user was right about the fold-back angle

D066 raised the flap stop to 179 degrees and said that laid the flap flat on the outside of the wall. That was wrong. Rotating about the crease axis, local +y maps to world (y,z) = (cos, sin): 0 degrees is shut over the opening, 90 is straight up, 180 points horizontally outward like a shelf, and only 270 hangs the flap down the outside of the wall. A carton opened right out is 270 from shut, which is what the user said.

At 270 the panel's thickness direction maps to world +y, inward, so a plate centred on the crease axis would sink half a board into the wall. The panel is now offset by -t/2 in local z, hanging on the outside of the axis, and the hinge heights move up by one board to keep the shut stacking, majors over minors: minors at H+t, majors at H+2t. Measured in 20260917T150421Z_ext1_carton_pull: the flap folds to 270.0, is released, stays at 268.97, its tip ends 99.5 mm below the crease, which is its whole length, and 1.79 mm clear of the wall face. The report also gives the angle the other way round, as the wall-to-flap angle a protractor at the crease would read, where shut is 90 and folded right out is 358.97.

Two smaller things came out of it. `opposite_minor_undisturbed` compared abs(angle) against 5 degrees while the untouched flap rests at its -5 degree stop, so it was knife-edge and failed on a flap that had not moved; it now asks whether the flap opened. And the claim that joint drag "drags with a constraint" was never established: the installed package names the setting SETTING_MOUSE_GRAB_WITH_FORCE and scales that force by pickingForce, but what the other mode does instead is in the closed binary. The wording in the code now says that.


## D068 — Export package, and the line between what the USD carries and what it cannot

User asked how to hand this to someone else as a USD, and whether the physics is in it. The honest answer is: most of it, but not the part that makes it a carton.

`scripts/pf-carton-export --run <id>` builds `exports/<name>/` and then opens the exported USD inside Isaac and reads its physics back, rather than asserting what should be there. Verified present in `carton.usda` for 20260917T150447Z: one articulation root, nine collidable plates, four PhysicsRevoluteJoints with axis, -5..270 limits, angular force drives whose per-degree stiffness converts back to the configured 0.1204 N.m/rad for every flap, drive damping, rest angle and force limit, PhysX joint friction and the static and dynamic friction efforts, rigid body masses, and the physics scene with gravity.

Absent, and stated as absent in both `physics_in_usd.json` and the README: the crease yield torque, the plastic viscosity and the softening rate. A USD drive has one rest angle attribute; making a fold permanent means moving that attribute every physics step against a yield rule, which no USD attribute expresses. Opened alone the file behaves as an articulated box with elastic hinges that spring back. The package therefore ships `crease_controller/` with the six modules the rule needs and a `load_in_isaacsim.py` entry, and the README says plainly which behaviour needs it. Panel deformation is absent entirely: the panels are rigid, so the carton cannot dent, crush, buckle or tear.

Two things were removed at the user's request: the joint-drag mouse mode, which took hold of the whole carton rather than the flap under the cursor, and the four edge-force sliders in the window. The ForceProbe class stays because the headless measurements use it; only its UI is gone. Two bugs were found on the way: `carton_usd_check` still asserted the old -5..100 limits, now read from config, and the readback loop shadowed the flap name with an attribute name, which silently skipped the stiffness comparison and made `gains_match_config` false.


## D069 — Workflow contracts separate from case and repair envelopes

Adopt parcel_forge.workflow_bundle/1 for task, parts, parameters, runtime and required checks. Existing case/1 and repair_proposal/2 remain distinct and unchanged. Capability registry distinguishes implemented historical proxies from unsupported behaviors; all new checks remain planned. P0 fixtures verify representability, not physics. This prevents metadata-only capability claims and silent task simplification. Evidence: runs/20260917T165040Z_wf_p0.


## D070 — One representative carton-and-keyboard package

User requested one meaningful scenario instead of a broad matrix. Use a parameterized rigid keyboard proxy (visual keys, collidable case) inside a four-flap carton. Fixed base is explicitly a laboratory opening fixture. External forces and constitutive callbacks produce opening, not angle commands. Passing this fixture must not mark payload_extraction implemented or claim image-to-3D, native GUI or real material calibration. Evidence: runs/20260917T235608Z_keyboard_package.


## D071 — Robot props require physical whole-body mobility evidence

The keyboard package used a fixed laboratory base and appeared glued to the floor in the user viewer. Change its generator to free base, reject fixed boundaries for move/extraction tasks, require structure.mobility, and accept only mobility_verified runs in the live loader. Check world-anchor joints, dynamic body enabled, and measured displacement under an external force without pose changes. Retain collision/gravity/friction; use base-local payload coordinates. Evidence: runs/20260918T001602Z_keyboard_package (12 N for 0.2 s, 0.213743 m horizontal displacement). GUI viewing and general indirect-anchor-chain analysis remain not_tested/not_implemented.

## D072 — Image intake and generated geometry are separate evidence stages

Use one standalone cordless drill for image-provider qualification, per user correction. Snapshot image/source declaration/bundle/registry/code hashes, enforce preflight and whole-object rigid scope before any provider handoff. Initial external artifact checker accepts OBJ and rejects flat referenced surfaces; this does not prove image generation, visual fidelity, material integrity or physics. Keep predicted PBR/physical parameters assumed; Marso is an external USD candidate rather than evidence of calibrated material behavior. Pin EmbodiedGen v2.1.0/f0124197888c2b733e4eaa65acd81ad9cfda3b79; no package changes in Isaac environment. See reports/development/2026-09-18_image_intake_marso.md.

## D073 — Qualified minimal image geometry backend before estimated-physics pipeline

Use pinned MIT TripoSR as one real-image geometry baseline, preserving EmbodiedGen as later enriched-pipeline candidate. Isolated torch2.8/cu128 environment; torchmcubes upstream copied with tracked C++17 compatibility patch for CUDA12.8 lerp conflict, and existing Python headers referenced read-only. Export embedded vertex-colored USD visual plus PhysX convexDecomposition rigid proxy, with assumed scale/mass/material and computed proxy inertia. Initial scene is exported after physics configuration, then relative references verified in a new directory/new process. Raw Kit exit0 with no result is failure (012442Z), never acceptance. Shape/contact fidelity/calibration/render/human viewing remain distinct from passed generation/physics/cold-load. Evidence: 012226Z_image_generation,012639Z_image_drill_usd,012704Z_image_drill_cold; report2026-09-18_image_drill_delivery.md.

## D074 — Thin shared Skill, dual intake and local machine binding (2026-09-18)

User authorized multi-input workflow and private GitHub push, including Codex/Claude Code reuse and preserving keyboard-carton quality. Keep one SKILL.md under .agents/skills; Claude project path uses a relative file symlink. Fixed image commands are dispatched by pf-workflow, one attempt, no automatic repair. Text entry captures a description and bundle, not arbitrary text-to-physics inference; unsupported capabilities stay blocked. Existing NVIDIA fixed-SHA adapter/state/repair contracts remain authoritative for their existing scope; new image route explicitly reports nvidia_validation not_tested. Local Isaac config overrides reference-machine inventory; metadata/API file probe is not a compatibility guarantee. Do not rewrite physical generators/thresholds. New raw runs/weights/venvs stay local; historical tracked evidence stays in history, selected new concise evidence is explicitly added. Cross-machine 5090 and actual two-agent Skill invocation need their own tests.

## D075 — Explicit image fragment cleanup and linear-color material graph (2026-09-18)
Human reported acceptable coarse shape but odd colors and loose fragments. Measure raw OBJ topology directly; trimesh split repair can add faces. Cleanup is generator postprocessing, explicit largest policy for this single rigid object, default keep; preserve raw and removed parts for human review. Image-derived RGB is treated as sRGB, converted to linear vertex primvars, with explicit PreviewSurface binding and assumed roughness/metallic. This is not calibrated albedo/PBR. Physics thresholds/collisions remain unchanged, original carton/keyboard core source hashes unchanged. Human appearance/render remain separate pending gates.
