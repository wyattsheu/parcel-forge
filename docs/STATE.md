# Current state
Updated: 2026-09-16 03:55 UTC (2026-09-16 11:55 Asia/Taipei)
Repository: /mnt/HDD4/wyattsheu/ITRI/parcel-forge
Branch / commit: master / fc38bca (before this doc commit)
Working tree: documentation updates pending commit at time of writing
Stage: S1
Status: done (verified)

## Verified
Each line below is backed by a saved run. Nothing here is inferred from source code.

- Read-only environment inventory and health report.
  `./scripts/pf doctor` -> overall=warn (the warn is "2 foreign GPU processes present", by design).
- Isaac Sim 6.0.1.0 launches headless from this repo, with livestream disabled.
- Finite-step PhysX simulation: 600 steps at dt=1/240 s, ended at sim_time 2.5250 s.
- Per-step read-back of position, orientation (w,x,y,z), linear and angular velocity, and sim time.
- Free fall matches theory: at t=0.1 s the cube fell 0.05109 m vs analytic 0.04905 m,
  error 0.00204 m against a 0.003 m tolerance. The error equals the expected
  semi-implicit Euler overshoot 0.5*g*dt*t, pinned in tests/test_free_fall_reference.py.
- The cube lands and stays: final z = 0.02000 m (exactly half its 0.04 m edge),
  final speed 0.000061 m/s, no NaN, no tunnelling.
- Offline PNG render of the real final scene: 1280x720, 106642 bytes,
  mean_r=226.8, distinct_r=98, blank-frame check passed.
- The agent opened that PNG and saw a cube resting on the floor with a cast shadow.
  This is agent-side viewing of a saved file, which is NOT the same as WebRTC viewing.
- 9 unit tests pass: `python3 -m unittest discover -s tests`.

## Not verified / not tested
- WebRTC viewing of a parcel-forge scene: **not_tested**. Livestream is never enabled
  (D003). Only the user can confirm this, and only for their own viewer.
- Isaac Sim official asset validation rules: not invoked (S3).
- USD file authoring and read-back: S1 builds the scene in memory; no .usda is
  written yet. Starts at S2/S3.
- Determinism across GPUs or drivers: not measured.

## Latest evidence
- Run: `runs/20260916T035235Z_s1_smoke/`
- Command: `./scripts/pf smoke`
- pf exit code 0; raw Isaac runtime exit code 0
- Profile: profiles/s1_smoke_v1.json (sha256 in the run manifest)
- Code version: recorded in `runs/20260916T035235Z_s1_smoke/manifest.json` as commit + dirty-diff hash
- Files: trajectory.csv (600 rows), renders/scene_final.png, s1_result.json,
  logs/isaac_runtime.log, summary.md, environment.json, manifest.json
- Coverage: proves physics, read-back, headless operation and offline render on
  this machine. Proves nothing about box geometry, USD asset files, fault
  detection, or WebRTC.

## Blockers and failed attempts
- Earlier run `runs/20260916T034844Z_s1_smoke` is kept on purpose: physics and the
  PNG succeeded but `s1_result.json` was missing, so `pf` exited 4
  (insufficient evidence) instead of reporting a pass. Cause: `SimulationApp.close()`
  terminates the process, so writes placed after it never ran. Fixed by writing all
  artefacts before closing; see `_close()` in src/parcel_forge/smoke_s1.py.
- Observation, cause unknown: the user's WebRTC viewer process changed PID during the
  first smoke run (old PID gone, new PID 2430488 started 11:49:48 local, log shows
  `READY - streaming`). parcel-forge never ran any start/stop script and never signalled
  any process. The viewer is live. Please confirm your own session is healthy.

## Next exact action
Start S2 by writing `src/parcel_forge/geometry.py` and its unit test, and confirm the
five-plate table reproduces interior dimensions Li=0.29, Wi=0.19, Hi=0.145 m
**before** touching the simulator. Card: docs/tasks/S2.md.

## Related task and decisions
- docs/tasks/S1.md (done), docs/tasks/S2.md (next)
- D001 standalone launcher, D002 6.0 experimental API, D003 livestream off,
  D004 stdlib PNG, D005 split collision/visual ground
