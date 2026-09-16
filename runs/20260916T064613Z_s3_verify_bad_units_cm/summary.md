# S3 build+validate 20260916T064613Z_s3_verify_bad_units_cm

- Case: **bad_units_cm**
- UTC: 2026-09-16T06:46:13Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `unit_mismatch`

| code | path | message |
| --- | --- | --- |
| unit_mismatch | `units.length` | this project works in SI only: expected 'm', got 'cm' |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
