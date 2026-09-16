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

## Related task and decisions
- docs/tasks/S1.md, S2.md, S3.md (all done), docs/tasks/S4.md (next)
- D001 standalone launcher, D002 6.0 experimental API, D003 livestream off,
  D004 stdlib PNG, D005 split collision/visual ground, D006 local-frame judgement,
  D007 two evidence views, D008 pxr without Kit, D009 invalid cases in a subdirectory
