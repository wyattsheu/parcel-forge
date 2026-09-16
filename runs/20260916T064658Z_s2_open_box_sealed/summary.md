# S2 open-box run 20260916T064658Z_s2_open_box_sealed

- Case: **open_box_sealed**  (fault: `sealed_lid`)
- Expected outcome: **at_mouth**
- Observed outcome: **at_mouth**
- UTC: 2026-09-16T06:47:13Z
- Command: `/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 /mnt/HDD4/wyattsheu/ITRI/parcel-forge/src/parcel_forge/box_s2.py --out /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T064658Z_s2_open_box_sealed --case /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T064658Z_s2_open_box_sealed/request.json --profile /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260916T064658Z_s2_open_box_sealed/profile.json`
- CWD: `/mnt/HDD4/wyattsheu/IsaacLab`  CUDA_VISIBLE_DEVICES=0
- Raw runtime exit code: 0
- parcel-forge exit code: 0

## Capability status (reported separately)

| capability | status | evidence |
| --- | --- | --- |
| static geometry read-back | pass | geometry_readback in s2_result.json |
| USD asset written | pass | asset.usda |
| physics execution | ran | trajectory.csv, 900 steps |
| local-frame outcome judgement | at_mouth | box local frame (origin = outer bottom face centre) |
| offline PNG render | ok | renders/open_box_sealed_interior_top.png, renders/open_box_sealed_side_low.png |
| WebRTC human view | not_tested | no agent evidence possible |

## Measured positions

- Final world position: [-7.248808486792768e-08, -9.365444242348531e-08, 0.3700000047683716]
- Final box-local position: [-7.248808486792768e-08, -9.365444242348531e-08, 0.17000000476837157]
- Lowest box-local z reached: 0.16866405606269835
- Final speed: 6.125469553736988e-05 m/s

Reason: probe rests at box-local z=0.17000 m, at or above the opening; it never entered the cavity (lowest local z reached 0.16866 m)

## Checks

| id | status | detail |
| --- | --- | --- |
| S2.plate_dimensions_match_spec | pass | largest world-size error 0.00000001 m on bottom (tolerance 0.0001 m), read back through the composed transform |
| S2.plate_count | pass | 6 colliders authored, spec says 6 |
| S2.no_rigid_body_on_fixed_box | pass | the S2 box is static: no RigidBodyAPI on the root, five separate box colliders instead of one convex hull |
| S2.no_nan | pass | all probe samples finite |
| S2.finite_steps | pass | executed 900/900 steps, ended at t=3.7750s |
| S2.outcome_matches_expectation | pass | expected 'at_mouth', observed 'at_mouth'. probe rests at box-local z=0.17000 m, at or above the opening; it never entered the cavity (lowest local z reached 0.16866 m) |
| S2.fault_not_silently_accepted | pass | fault 'sealed_lid' produced 'at_mouth'; a fault classified as 'inside' would mean the check is blind |
| S2.render_png_not_blank | pass | interior_top=226265 B mean_r=227.7013; side_low=136853 B mean_r=223.6816 |
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
- `renders/open_box_sealed_interior_top.png`
- `renders/open_box_sealed_side_low.png`
- `logs/isaac_runtime.log`
