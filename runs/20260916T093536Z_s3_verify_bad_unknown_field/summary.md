# S3 build+validate 20260916T093536Z_s3_verify_bad_unknown_field

- Case: **bad_unknown_field**
- UTC: 2026-09-16T09:35:36Z
- parcel-forge exit code: 2

## Schema

Verdict: **rejected**
Error classes: `unknown_field`

| code | path | message |
| --- | --- | --- |
| unknown_field | `colour` | field is not part of the schema; known fields: ['asset_type', 'case_id', 'description', 'expected_outcome', 'frame', 'geometry', 'intended_task', 'physics', 'placement', 'probe', 'provenance', 'schema', 'seed', 'units'] |

No USD was authored and no simulator interpreter was started.

## Files

- `environment.json`
- `manifest.json`
- `request.json`
- `schema_findings.json`
