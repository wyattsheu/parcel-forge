# S2 open-box run 20260916T053109Z_s2_open_box_no_bottom

- Case: **open_box_no_bottom**  (fault: `missing_bottom`)
- Expected outcome: **fell_through**
- Observed outcome: **fell_through**
- UTC: 2026-09-16T05:31:23Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/box_s2.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T053109Z_s2_open_box_no_bottom --case /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T053109Z_s2_open_box_no_bottom/request.json --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T053109Z_s2_open_box_no_bottom/profile.json`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 0

## Capability status (reported separately)

| capability | status | evidence |
| --- | --- | --- |
| static geometry read-back | pass | geometry_readback in s2_result.json |
| USD asset written | pass | asset.usda |
| physics execution | ran | trajectory.csv, 900 steps |
| local-frame outcome judgement | fell_through | box local frame (origin = outer bottom face centre) |
| offline PNG render | ok | renders/open_box_no_bottom_final.png |
| WebRTC human view | not_tested | no agent evidence possible |

## Measured positions

- Final world position: [-2.1636094515997684e-06, 2.364902002227609e-06, 0.019999999552965164]
- Final box-local position: [-2.1636094515997684e-06, 2.364902002227609e-06, -0.18000000044703485]
- Lowest box-local z reached: -0.18000000417232515
- Final speed: 6.130950052488512e-05 m/s

Reason: probe came to rest at box-local z=-0.18000 m, below the box itself; the surface supporting it is not the box floor

## Checks

| id | status | detail |
| --- | --- | --- |
| S2.plate_dimensions_match_spec | pass | largest world-size error 0.00000001 m on wall_y_pos (tolerance 0.0001 m), read back through the composed transform |
| S2.plate_count | pass | 4 colliders authored, spec says 4 |
| S2.no_rigid_body_on_fixed_box | pass | the S2 box is static: no RigidBodyAPI on the root, five separate box colliders instead of one convex hull |
| S2.no_nan | pass | all probe samples finite |
| S2.finite_steps | pass | executed 900/900 steps, ended at t=3.7750s |
| S2.outcome_matches_expectation | pass | expected 'fell_through', observed 'fell_through'. probe came to rest at box-local z=-0.18000 m, below the box itself; the surface supporting it is not the box floor |
| S2.fault_not_silently_accepted | pass | fault 'missing_bottom' produced 'fell_through'; a fault classified as 'inside' would mean the check is blind |
| S2.render_png_not_blank | pass | 1280x720 png, 287203 bytes, mean_r=220.7959, distinct_r=78 |
| S2.webrtc_human_view | not_tested | livestream never enabled; only a human can confirm a WebRTC view |

**Verdict: pass**

## Files

- `asset.usda`
- `environment.json`
- `manifest.json`
- `profile.json`
- `request.json`
- `s2_result.json`
- `summary.md`
- `trajectory.csv`
- `renders/open_box_no_bottom_final.png`
- `logs/isaac_runtime.log`
