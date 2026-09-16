# S1 smoke run 20260916T034844Z_s1_smoke

- UTC: 2026-09-16T03:51:55Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/smoke_s1.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T034844Z_s1_smoke --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T034844Z_s1_smoke/profile.json`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 4

## Capability status (each reported separately)

| capability | status | evidence |
| --- | --- | --- |
| physics execution | blocked | in-runtime script produced no result file |
| state read-back | blocked | none |
| headless | blocked | none |
| offline PNG render | blocked | none |
| WebRTC human view | not_tested | none |

See `logs/isaac_runtime.log` for the failure.

## Files

- `environment.json`
- `manifest.json`
- `profile.json`
- `summary.md`
- `trajectory.csv`
- `renders/scene_final.png`
- `logs/isaac_runtime.log`
