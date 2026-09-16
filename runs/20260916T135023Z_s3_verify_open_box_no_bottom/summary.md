# S3 build+validate 20260916T135023Z_s3_verify_open_box_no_bottom

- Case: **open_box_no_bottom**
- UTC: 2026-09-16T13:50:23Z
- parcel-forge exit code: 0

## Built asset

- File: `asset.usda`  (defaultPrim `/OpenBox`)
- Plates: 4, body_mode `static`
- Interior: 0.2900 x 0.1900 x 0.1450 m, floor at local z = 0.0050 m
- Plate volume: 0.0007105000 m^3

## Static validation (G1)

Profile: `static_usd_v1`  tolerance 0.0001 m

| rule | status | detail |
| --- | --- | --- |
| G1.stage_opens | pass | stage opened from the written file |
| G1.no_missing_references | pass | 0 external dependency/ies, 0 unresolvable |
| G1.default_prim | pass | defaultPrim is /OpenBox, expected /OpenBox |
| G1.stage_units_and_axis | pass | metersPerUnit=1.0, kilogramsPerUnit=1.0, upAxis=Z; expected 1.0 / 1.0 / Z |
| G1.plate_dimensions | pass | largest world size/centre error 0.0000000083 m on wall_y_pos (tolerance 0.0001 m), read back through the composed transform |
| G1.collider_count | pass | 4 colliders, expected 4 |
| G1.rigid_body_count | pass | 0 rigid bodies, expected 0 for body_mode=static |
| G1.no_nested_rigid_bodies | pass | no rigid body is nested inside another |
| G1.unique_prim_names | pass | all prim names unique |
| G1.finite_positive_mass | pass | every authored mass is finite and > 0 |
| G7.official_validator_can_fail | pass | the official engine reported 3 failure(s) on a deliberately broken asset: DefaultPrimChecker, PrimEncapsulationChecker, StageMetadataChecker |
| G1.official_isaac_asset_validation | pass | omni.asset_validator (usd_validation_nvidia) 1.19.3: 41 rules ran, 0 failure(s), 0 warning(s). NVIDIA's generic USD rule set. It says nothing about whether this box can hold an object: cavity containment is proven by the S2 drop test, not by a clean validator report. |

**Verdict: pass** (0 failed, 0 blocked)

## Files

- `asset.usda`
- `build_manifest.json`
- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
- `static_profile.json`
- `validation.json`
- `validator_self_test_broken.usda`
- `logs/build.log`
- `logs/validate.log`
