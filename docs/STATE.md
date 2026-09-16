# Current state
Updated: 2026-09-16 05:40 UTC (2026-09-16 13:40 Asia/Taipei)
Repository: /mnt/HDD4/wyattsheu/ITRI/parcel-forge
Branch / commit: master / a4a2e41 (before this doc commit)
Working tree: documentation updates pending commit at time of writing
Stage: S2
Status: done (verified)

## Verified
Every line is backed by a saved run. Nothing is inferred from source code.

### S2 open box (this session)
- `./scripts/pf box --all` -> pf exit 0. Suite table:
  `runs/20260916T053351Z_s2_open_box_sealed_suite.md`

  | case | expected | observed | box-local final z |
  | --- | --- | --- | --- |
  | open_box_normal | inside | inside | 0.02500 m (wall thickness 0.005 + half probe 0.02) |
  | open_box_sealed | at_mouth | at_mouth | 0.17000 m; lowest reached 0.16866 m, never entered |
  | open_box_no_bottom | fell_through | fell_through | -0.18000 m (world z 0.02, on the world floor) |

- Both deliberate faults were caught, and neither was classified `inside`.
- Plate dimensions read back from the authored stage through the composed
  transform: largest error 1e-8 m against a 1e-4 m tolerance, in all three cases.
- Collider count matches the spec per case (5 normal, 6 sealed, 4 missing-bottom);
  no RigidBodyAPI on the static box root; five separate box colliders, no convex hull.
- 900/900 steps, no NaN, clean shutdown in every case.
- Two evidence renders per case (interior_top, side_low), all non-blank. The agent
  opened three of them: the normal case shows the cube on the interior floor, the
  sealed case shows it sitting on the closed lid, the missing-bottom case shows the
  bottomless box floating with the cube on the floor beneath it.
- Geometry maths matches the handbook's independent calculation exactly:
  total plate volume 0.0010105 m^3 (section 19), interior 0.29 x 0.19 x 0.145 m.
- 37 offline unit tests pass: `python3 -m unittest discover -s tests`.

### S1 baseline (re-verified this session)
- `./scripts/pf smoke` -> pf exit 0, reproduced identically:
  `runs/20260916T042007Z_s1_smoke/`. Free-fall error 0.00204 m vs 0.003 m tolerance,
  final z exactly 0.02000 m, render non-blank.

## Not verified / not tested
- WebRTC viewing of a parcel-forge scene: **not_tested** by design (D003).
- `asset.usda` is a flattened Kit stage: it carries Kit's `/Render` scope and has
  no `defaultPrim` of our own. A clean asset layer with explicit units is S3 work.
- No input schema yet: case files are read as plain JSON, unknown fields are not
  rejected, and illegal specs are only caught by the geometry rules. That is S3.
- Isaac Sim official asset-validation rules: not invoked (S3).
- Mass, centre of mass and inertia: authored only for the probe; the box is static
  and has none. That is S4.

## Latest evidence
- Runs: `runs/20260916T053320Z_s2_open_box_no_bottom/`,
  `runs/20260916T053335Z_s2_open_box_normal/`,
  `runs/20260916T053351Z_s2_open_box_sealed/`
- Each contains: manifest.json (code commit + dirty-diff hash, case/profile/script
  hashes, command, both exit codes), environment.json, request.json, profile.json,
  asset.usda, trajectory.csv (world + box-local columns), s2_result.json,
  renders/ (two PNGs), logs/, summary.md
- Profile: profiles/open_box_v1.json
- Coverage: proves box construction, static geometry read-back, cavity containment
  and fault detection for one fixed size. Proves nothing about other sizes, dynamic
  boxes, mass properties, or nine-point placement.

## Blockers and failed attempts
- `runs/20260916T053123Z_s2_open_box_normal/` carries `aborted.json`: I stopped my
  own suite run mid-flight to switch evidence rendering from one view to two. It is
  not evidence. No foreign process was signalled.
- Earlier S1 failure `runs/20260916T034844Z_s1_smoke/` remains on record (artefacts
  written after `SimulationApp.close()` never happened; fixed).
- Open observation from the previous session: the user's WebRTC viewer changed PID
  during the first smoke run. It has been up and streaming since; cause still unknown.

## Next exact action
Start S3: write `src/parcel_forge/schema.py` and its unit tests, so an illegal case
file is rejected with a named error class before any simulator launch.
Card: docs/tasks/S3.md.

## Related task and decisions
- docs/tasks/S1.md (done), docs/tasks/S2.md (done), docs/tasks/S3.md (next)
- D001 standalone launcher, D002 6.0 experimental API, D003 livestream off,
  D004 stdlib PNG, D005 split collision/visual ground, D006 local-frame judgement,
  D007 two evidence views
