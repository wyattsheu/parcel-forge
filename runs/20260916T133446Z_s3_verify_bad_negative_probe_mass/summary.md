# S3 build+validate 20260916T133446Z_s3_verify_bad_negative_probe_mass

- Case: **bad_negative_probe_mass**
- UTC: 2026-09-16T13:34:46Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `value_out_of_range`

| code | path | message |
| --- | --- | --- |
| value_out_of_range | `probe.mass_kg` | must be > 0.0, got -0.05 |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
