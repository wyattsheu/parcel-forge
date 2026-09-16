# S3 build+validate 20260916T135027Z_s3_verify_bad_wall_too_thick

- Case: **bad_wall_too_thick**
- UTC: 2026-09-16T13:50:27Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `geometry_not_constructible`

| code | path | message |
| --- | --- | --- |
| geometry_not_constructible | `geometry` | L must be > 2*t: 0.008 <= 0.01 |
| geometry_not_constructible | `probe.size_m` | probe edge 0.04 m does not fit the cavity -0.002 x 0.19 m |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
