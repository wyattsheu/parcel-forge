# S3 build+validate 20260916T064610Z_s3_verify_open_box_normal

- Case: **open_box_normal**
- UTC: 2026-09-16T06:46:10Z
- parcel-forge exit code: 0

## Built asset

- File: `asset.usda`  (defaultPrim `/OpenBox`)
- Plates: 5, body_mode `static`
- Interior: 0.2900 x 0.1900 x 0.1450 m, floor at local z = 0.0050 m
- Plate volume: 0.0010105000 m^3

## Static validation (G1)

Profile: `static_usd_v1`  tolerance 0.0001 m

| rule | status | detail |
| --- | --- | --- |
| G1.stage_opens | pass | stage opened from the written file |
| G1.no_missing_references | pass | 0 external dependency/ies, 0 unresolvable |
| G1.default_prim | pass | defaultPrim is /OpenBox, expected /OpenBox |
| G1.stage_units_and_axis | pass | metersPerUnit=1.0, kilogramsPerUnit=1.0, upAxis=Z; expected 1.0 / 1.0 / Z |
| G1.plate_dimensions | pass | largest world size/centre error 0.0000000119 m on bottom (tolerance 0.0001 m), read back through the composed transform |
| G1.collider_count | pass | 5 colliders, expected 5 |
| G1.rigid_body_count | pass | 0 rigid bodies, expected 0 for body_mode=static |
| G1.no_nested_rigid_bodies | pass | no rigid body is nested inside another |
| G1.unique_prim_names | pass | all prim names unique |
| G1.finite_positive_mass | pass | every authored mass is finite and > 0 |
| G1.official_isaac_asset_validation | blocked | Isaac Sim 6.0's own asset-validation rule set has not been invoked by this tool yet (planned work). These are parcel-forge's internal checks, and passing them is NOT a SimReady certification. |

**Verdict: pass** (0 failed, 1 blocked)

## Files

- `asset.usda`
- `build_manifest.json`
- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
- `static_profile.json`
- `validation.json`
- `logs/build.log`
- `logs/validate.log`
