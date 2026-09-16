# D017 timestep sweep

Case: open_box_normal
Generated: 2026-09-16T14:13:10Z

| dt | expected | observed | box-local z | verdict | run |
| --- | --- | --- | --- | --- | --- |
| 1/60 | inside | inside | 0.02500 | pass | `runs/20260916T141233Z_s2_open_box_normal` |
| 1/120 | inside | inside | 0.02500 | pass | `runs/20260916T141245Z_s2_open_box_normal` |
| 1/240 | inside | inside | 0.02500 | pass | `runs/20260916T141258Z_s2_open_box_normal` |

Containment must hold at every timestep. A result that depends on dt is a property of the solver settings, not of the asset.
