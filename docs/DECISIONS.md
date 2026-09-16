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

Status: open finding, not yet addressed
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
