# Current state
Updated: 2026-09-16 06:55 UTC (2026-09-16 14:55 Asia/Taipei)
Repository: /mnt/HDD4/wyattsheu/ITRI/parcel-forge
Branch / commit: master / e7532ac (before this doc commit)
Working tree: documentation updates pending commit at time of writing
Stage: S3
Status: done (verified)

## Verified
Every line is backed by a saved run under runs/. Nothing is inferred from source code.

### S3 schema, USD authoring, static validation (this session)
- `./scripts/pf verify --all` -> exit 0 in **4.2 s**, 13 cases, no GPU, Kit never started.
  Suite table: `runs/20260916T064613Z_s3_verify_bad_wall_too_thick_suite.md`
- 6 legal cases each authored a clean USD asset and passed all 10 graded G1 rules:
  defaultPrim `/OpenBox`, metersPerUnit=1, kilogramsPerUnit=1, upAxis=Z, per-plate
  world dimensions read back from the output stage (error ~1.2e-8 m against a
  1e-4 m tolerance), collider count, rigid-body count, no nested rigid bodies,
  unique prim names, finite positive mass.
- 7 invalid cases were each rejected **before any interpreter for the simulator
  started**, each with its declared error class: geometry_not_constructible (x2),
  unknown_field, value_out_of_range, enum_invalid, value_not_finite, unit_mismatch.
- `./scripts/pf box --all` -> exit 0 over 6 legal cases. Suite table:
  `runs/20260916T064747Z_s2_open_box_thick_wall_suite.md`

  | case | expected | observed | box-local final z |
  | --- | --- | --- | --- |
  | open_box_normal | inside | inside | 0.02500 m |
  | open_box_sealed | at_mouth | at_mouth | 0.17000 m |
  | open_box_no_bottom | fell_through | fell_through | -0.18000 m |
  | open_box_small | inside | inside | (t=0.003) |
  | open_box_tall | inside | inside | (0.20 x 0.20 x 0.30 m) |
  | open_box_thick_wall | inside | inside | 0.04000 m = t + probe/2 with t=0.02 |

- 57 offline unit tests pass: `python3 -m unittest discover -s tests`.

### Earlier stages, re-verified this session
- S1 `./scripts/pf smoke`: reproduced identically (`runs/20260916T042007Z_s1_smoke/`).
- S2 fault detection: unchanged, both faults still caught.

## Fixed this session (2026-09-16, later)

**Bug found by the user actually trying WebRTC viewing**, exactly the gap S1-S3
left open ("WebRTC viewing: not_tested" was true because nobody had tried it).

- S2's exported \`asset.usda\` never set \`defaultPrim\`. The user's known-good
  WebRTC viewer loads files by USD *reference*, which resolves through
  \`defaultPrim\`; without it the reference resolved to nothing. The viewer's own
  report proved it: \`bbox size = 0.0000 x 0.0000 x 0.0000, top-level prims = []\`.
  Fixed in \`IsaacSimRuntime.export_stage()\` (D013); regression test in
  \`tests/test_export_defaultprim.py\` first reproduces the failure with pxr
  directly, then proves the fix, then proves our method call fixes it too.
- The ground plane's *visible* slab was sized off the 20 m physics collider, so
  any viewer auto-framing on world bounds showed a wall of grey next to a 0.3 m
  box. Now sized off the box itself (D014).
- Verified without Kit: referencing the regenerated
  \`runs/20260916T133357Z_s2_open_box_normal/asset.usda\` the same way the viewer
  does resolves 13 prims including all five box colliders (previously 0).
- All 6 S2 cases regenerated with the fix, all pass: table in
  \`runs/20260916T133552Z_s2_open_box_thick_wall_suite.md\`. \`pf verify --all\`
  (13 cases, unaffected since S3's \`usd_author.py\` always set defaultPrim) and the
  full offline suite (60 tests, 3 correctly skipped without pxr) both still pass.
### Second round of the same investigation (user reported the cube did not fall)
- With defaultPrim fixed the box rendered correctly, but the probe hung frozen in
  mid-air. Two further causes, both found by measurement, not guesswork:
  - The PhysicsScene lived at `/PhysicsScene`, a sibling of `/World`, so a
    reference dropped it: the referencing stage reported zero physics scenes and
    the probe never moved. Fixed by relocating it under the default prim (D015).
  - PhysX never writes results back to USD. After 3 s the tensor API read the
    probe at z=0.22500 while USD still read 0.47000, and the user's viewer renders
    from USD. Each run now also writes `scene_final.usda` carrying the pose
    measured in that run (D016).
- Verified per case that `scene_final.usda` reads back the measured outcome in USD:
  normal/tall 0.22500, small 0.22300, thick_wall 0.24000, sealed 0.37000 (on the
  lid), no_bottom 0.02000 (world floor). All six match their recorded verdict.
- **New open finding D017**: the S2 containment result is dt-dependent. At
  dt = 1/60 the probe tunnels through the 5 mm bottom plate and lands on the world
  floor instead of inside the box. It is correct at the project's 1/240. Carried
  into docs/tasks/S4.md; raising dt to make it pass is explicitly not acceptable.
- 64 offline tests pass (7 skipped without pxr, all 64 run under the Isaac venv).

- **WebRTC human confirmation is still outstanding**: the fix is verified by USD
  composition semantics and by pf's own renders, not yet by the user actually
  seeing it stream. That is the literal next action.

## Not verified / not tested
- **Isaac Sim's official asset-validation rule set: still not invoked.** Every
  validation.json reports `G1.official_isaac_asset_validation` as `blocked` and
  states that passing parcel-forge's internal rules is not a SimReady certification.
- WebRTC viewing of a parcel-forge scene: **not_tested** by design (D003).
- Mass, centre of mass and inertia of the box: not computed or authored. The box is
  static and `usd_author` accepts `body_mode="dynamic"` but nobody has run it. S4.
- Coverage is one drop point per case. Nine-point placement and side-wall blocking
  tests are S4.
- Contact settings (contact offset, rest offset, friction, restitution) are PhysX
  defaults; they are not yet recorded per run. S4.
- Determinism across GPUs or drivers: not measured.

## Latest evidence
- S3 runs: `runs/20260916T0646*_s3_verify_*/` (13 directories), each with
  request.json, schema_findings.json, asset.usda + build_manifest.json (legal cases),
  static_profile.json, validation.json, manifest.json, logs/, summary.md
- S2 runs: `runs/20260916T064*_s2_*/` (6 directories) with trajectory.csv,
  two renders each, s2_result.json, manifest.json, summary.md
- Profiles: profiles/static_usd_v1.json, profiles/open_box_v1.json, profiles/s1_smoke_v1.json
- Coverage: proves specification rejection, deterministic asset authoring, static
  read-back, and cavity containment across four box sizes. Proves nothing about
  mass properties, dynamic boxes, placement coverage, or official validation.

## Blockers and failed attempts
- `runs/20260916T053123Z_s2_open_box_normal/` carries `aborted.json` (I stopped my
  own run to switch to two evidence views). Not evidence.
- `runs/20260916T034844Z_s1_smoke/` remains on record as the S1 write-ordering bug.
- Open observation from the first session: the user's WebRTC viewer changed PID
  during the first smoke run. It has been up and streaming since; cause unknown.

## Next exact action
Start S4: write `src/parcel_forge/mass_properties.py` and its unit test against the
handbook section 19 table (total plate volume 0.0010105 m^3, COM z = 0.0552337952 m,
Ixx/Iyy/Izz = 0.0016619320 / 0.0027588147 / 0.0034580587 kg m^2) **before** touching
the simulator. Card: docs/tasks/S4.md.

## Method sources
- \`docs/METHODS.md\` records, per cited source, the mechanism read, what was
  implemented, where it lives, and what was deliberately not taken. Written from the
  sources themselves on 2026-09-16, not from summaries.

## Related task and decisions
- docs/tasks/S1.md, S2.md, S3.md (all done), docs/tasks/S4.md (next), S5.md (drafted)
- D001 standalone launcher, D002 6.0 experimental API, D003 livestream off,
  D004 stdlib PNG, D005 split collision/visual ground, D006 local-frame judgement,
  D007 two evidence views, D008 pxr without Kit, D009 invalid cases in a subdirectory,
  D010 official validator + G7 reliability check, D011 version-matched API lookup
  (not yet implemented), D012 a critic may never upgrade a verdict
