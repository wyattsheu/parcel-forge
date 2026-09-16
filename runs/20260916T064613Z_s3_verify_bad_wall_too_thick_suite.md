# S3 case suite (schema -> USD -> static validation)

Generated: 2026-09-16T06:46:13Z

| case | expected | observed | verdict | run |
| --- | --- | --- | --- | --- |
| open_box_no_bottom | built + G1 pass | pass | pass | `runs/20260916T064609Z_s3_verify_open_box_no_bottom` |
| open_box_normal | built + G1 pass | pass | pass | `runs/20260916T064610Z_s3_verify_open_box_normal` |
| open_box_sealed | built + G1 pass | pass | pass | `runs/20260916T064610Z_s3_verify_open_box_sealed` |
| open_box_small | built + G1 pass | pass | pass | `runs/20260916T064611Z_s3_verify_open_box_small` |
| open_box_tall | built + G1 pass | pass | pass | `runs/20260916T064611Z_s3_verify_open_box_tall` |
| open_box_thick_wall | built + G1 pass | pass | pass | `runs/20260916T064612Z_s3_verify_open_box_thick_wall` |
| bad_fault_enum | rejected: enum_invalid | rejected: enum_invalid | pass | `runs/20260916T064612Z_s3_verify_bad_fault_enum` |
| bad_negative_probe_mass | rejected: value_out_of_range | rejected: value_out_of_range | pass | `runs/20260916T064612Z_s3_verify_bad_negative_probe_mass` |
| bad_non_finite_height | rejected: value_not_finite | rejected: value_not_finite | pass | `runs/20260916T064612Z_s3_verify_bad_non_finite_height` |
| bad_probe_too_big | rejected: geometry_not_constructible | rejected: geometry_not_constructible | pass | `runs/20260916T064613Z_s3_verify_bad_probe_too_big` |
| bad_units_cm | rejected: unit_mismatch | rejected: unit_mismatch | pass | `runs/20260916T064613Z_s3_verify_bad_units_cm` |
| bad_unknown_field | rejected: unknown_field | rejected: unknown_field | pass | `runs/20260916T064613Z_s3_verify_bad_unknown_field` |
| bad_wall_too_thick | rejected: geometry_not_constructible | rejected: geometry_not_constructible | pass | `runs/20260916T064613Z_s3_verify_bad_wall_too_thick` |

An invalid case that is ACCEPTED means the schema is blind, not that the specification is fine.
