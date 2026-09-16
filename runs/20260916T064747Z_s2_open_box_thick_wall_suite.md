# S2 case suite

Generated: 2026-09-16T06:48:01Z

| case | expected | observed | verdict | pf exit | run |
| --- | --- | --- | --- | --- | --- |
| open_box_no_bottom | fell_through | fell_through | pass | 0 | `runs/20260916T064623Z_s2_open_box_no_bottom` |
| open_box_normal | inside | inside | pass | 0 | `runs/20260916T064640Z_s2_open_box_normal` |
| open_box_sealed | at_mouth | at_mouth | pass | 0 | `runs/20260916T064658Z_s2_open_box_sealed` |
| open_box_small | inside | inside | pass | 0 | `runs/20260916T064713Z_s2_open_box_small` |
| open_box_tall | inside | inside | pass | 0 | `runs/20260916T064732Z_s2_open_box_tall` |
| open_box_thick_wall | inside | inside | pass | 0 | `runs/20260916T064747Z_s2_open_box_thick_wall` |

A fault case whose observed outcome is `inside` means the check is blind, not that the asset is good.
