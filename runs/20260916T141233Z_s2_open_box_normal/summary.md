# S2 open-box run 20260916T141233Z_s2_open_box_normal

- Case: **open_box_normal**  (fault: `none`)
- Expected outcome: **inside**
- Observed outcome: **inside**
- UTC: 2026-09-16T14:12:45Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/box_s2.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141233Z_s2_open_box_normal --case /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141233Z_s2_open_box_normal/request.json --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141233Z_s2_open_box_normal/profile.json --dt 0.016666666666666666`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 0

## Capability status (reported separately)

| capability | status | evidence |
| --- | --- | --- |
| static geometry read-back | pass | geometry_readback in s2_result.json |
| USD asset written | pass | asset.usda |
| physics execution | ran | trajectory.csv, 225 steps |
| local-frame outcome judgement | inside | box local frame (origin = outer bottom face centre) |
| offline PNG render | ok | renders/open_box_normal_interior_top.png, renders/open_box_normal_side_low.png |
| WebRTC human view | not_tested | no agent evidence possible |

## Measured positions

- Final world position: [-1.1623419595707674e-06, -1.5016701127024135e-06, 0.22499999403953552]
- Final box-local position: [-1.1623419595707674e-06, -1.5016701127024135e-06, 0.02499999403953551]
- Lowest box-local z reached: 0.022024977207183827
- Final speed: 0.0002456336160327151 m/s

Reason: probe rests on the interior floor at box-local z=0.02500 m (expected 0.02500 m) and inside the cavity footprint

## Checks

| id | status | detail |
| --- | --- | --- |
| S2.plate_dimensions_match_spec | pass | largest world-size error 0.00000001 m on bottom (tolerance 0.0001 m), read back through the composed transform |
| S2.plate_count | pass | 5 colliders authored, spec says 5 |
| S2.no_rigid_body_on_fixed_box | pass | the S2 box is static: no RigidBodyAPI on the root, five separate box colliders instead of one convex hull |
| S2.no_nan | pass | all probe samples finite |
| S2.finite_steps | pass | executed 225/225 steps, ended at t=3.8000s |
| S2.outcome_matches_expectation | pass | expected 'inside', observed 'inside'. probe rests on the interior floor at box-local z=0.02500 m (expected 0.02500 m) and inside the cavity footprint |
| S2.render_png_not_blank | pass | interior_top=419802 B mean_r=213.3346; side_low=121964 B mean_r=221.3181 |
| S2.webrtc_human_view | not_tested | livestream never enabled; only a human can confirm a WebRTC view |

**Verdict: pass**

## Files

- `asset.usda`
- `environment.json`
- `manifest.json`
- `profile.json`
- `request.json`
- `s2_result.json`
- `scene_final.usda`
- `summary.md`
- `trajectory.csv`
- `renders/open_box_normal_interior_top.png`
- `renders/open_box_normal_side_low.png`
- `logs/isaac_runtime.log`
