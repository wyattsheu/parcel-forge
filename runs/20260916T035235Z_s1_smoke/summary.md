# S1 smoke run 20260916T035235Z_s1_smoke

- UTC: 2026-09-16T03:52:52Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/smoke_s1.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T035235Z_s1_smoke --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T035235Z_s1_smoke/profile.json`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 0

## Capability status (each reported separately)

| capability | status | evidence |
| --- | --- | --- |
| physics execution | ran | trajectory.csv, 600 steps, sim_time_end=2.525 s |
| state read-back | ok | trajectory.csv columns position_m,orientation_wxyz,linear_velocity_mps,angular_velocity_radps |
| headless (no GUI, no livestream) | pass | launched with SimulationApp(headless=True), livestream never enabled |
| offline PNG render | ok | renders/scene_final.png |
| WebRTC human view | not_tested | no agent evidence possible; a human must look |

## Checks

| id | status | detail |
| --- | --- | --- |
| S1.finite_steps | pass | executed 600/600 steps, ended at t=2.5250s |
| S1.no_nan | pass | all pose/velocity samples finite |
| S1.free_fall_matches_analytic | pass | at t=0.1000s fell 0.05109 m, analytic 0.04905 m, error 0.00204 m (tolerance 0.003 m) |
| S1.cube_rests_on_ground | pass | final z=0.02000 m, expected 0.02000 m (half edge), error 0.00000 m (tolerance 0.002 m) |
| S1.settled | pass | final |v|=0.000061 m/s (tolerance 0.01 m/s) |
| S1.no_tunneling | pass | final z=0.02000 m is above the ground plane |
| S1.render_png_not_blank | pass | 1280x720 png, 106642 bytes, mean_r=226.8166, distinct_r=98 |
| S1.webrtc_human_view | not_tested | this run never enabled livestream; only a human can confirm a WebRTC view |

**Verdict: pass**

## Files

- `environment.json`
- `manifest.json`
- `profile.json`
- `s1_result.json`
- `summary.md`
- `trajectory.csv`
- `renders/scene_final.png`
- `logs/isaac_runtime.log`
