# S3 build+validate 20260916T133446Z_s3_verify_bad_non_finite_height

- Case: **bad_non_finite_height**
- UTC: 2026-09-16T13:34:46Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `value_not_finite`

| code | path | message |
| --- | --- | --- |
| value_not_finite | `geometry.outer_size_m[2]` | value must be finite, got inf |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
