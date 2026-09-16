# S3 build+validate 20260916T064612Z_s3_verify_bad_fault_enum

- Case: **bad_fault_enum**
- UTC: 2026-09-16T06:46:12Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `enum_invalid`

| code | path | message |
| --- | --- | --- |
| enum_invalid | `geometry.fault` | must be one of ['none', 'sealed_lid', 'missing_bottom'], got 'open_the_lid_a_bit' |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
