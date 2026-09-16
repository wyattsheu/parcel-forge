# S2 case suite

Generated: 2026-09-16T05:34:07Z

| case | expected | observed | verdict | pf exit | run |
| --- | --- | --- | --- | --- | --- |
| open_box_no_bottom | fell_through | fell_through | pass | 0 | `runs/20260916T053320Z_s2_open_box_no_bottom` |
| open_box_normal | inside | inside | pass | 0 | `runs/20260916T053335Z_s2_open_box_normal` |
| open_box_sealed | at_mouth | at_mouth | pass | 0 | `runs/20260916T053351Z_s2_open_box_sealed` |

A fault case whose observed outcome is `inside` means the check is blind, not that the asset is good.
