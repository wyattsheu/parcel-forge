# S2 open-box run 20260916T141425Z_s2_open_box_small

- Case: **open_box_small**  (fault: `none`)
- Expected outcome: **inside**
- Observed outcome: **inside**
- UTC: 2026-09-16T14:14:38Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/box_s2.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141425Z_s2_open_box_small --case /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141425Z_s2_open_box_small/request.json --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T141425Z_s2_open_box_small/profile.json`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 0

## Capability status (reported separately)

| capability | status | evidence |
| --- | --- | --- |
| static geometry read-back | pass | geometry_readback in s2_result.json |
| USD asset written | pass | asset.usda |
| physics execution | ran | trajectory.csv, 900 steps |
| local-frame outcome judgement | inside | box local frame (origin = outer bottom face centre) |
| offline PNG render | ok | renders/open_box_small_interior_top.png, renders/open_box_small_side_low.png |
| WebRTC human view | not_tested | no agent evidence possible |

## Measured positions

- Final world position: [-7.09124492459523e-08, -9.334354444945347e-08, 0.22299998998641968]
- Final box-local position: [-7.09124492459523e-08, -9.334354444945347e-08, 0.022999989986419667]
- Lowest box-local z reached: 0.022999945282936085
- Final speed: 6.180342637540627e-05 m/s

Reason: probe rests on the interior floor at box-local z=0.02300 m (expected 0.02300 m) and inside the cavity footprint

## Checks

| id | status | detail |
| --- | --- | --- |
| S2.plate_dimensions_match_spec | pass | largest world-size error 0.00000001 m on wall_y_pos (tolerance 0.0001 m), read back through the composed transform |
| S2.plate_count | pass | 5 colliders authored, spec says 5 |
| S2.no_rigid_body_on_fixed_box | pass | the S2 box is static: no RigidBodyAPI on the root, five separate box colliders instead of one convex hull |
| S2.no_nan | pass | all probe samples finite |
| S2.finite_steps | pass | executed 900/900 steps, ended at t=3.7750s |
| S2.outcome_matches_expectation | pass | expected 'inside', observed 'inside'. probe rests on the interior floor at box-local z=0.02300 m (expected 0.02300 m) and inside the cavity footprint |
| S2.render_png_not_blank | pass | interior_top=214638 B mean_r=223.8442; side_low=42921 B mean_r=223.6932 |
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
- `renders/open_box_small_interior_top.png`
- `renders/open_box_small_side_low.png`
- `logs/isaac_runtime.log`
