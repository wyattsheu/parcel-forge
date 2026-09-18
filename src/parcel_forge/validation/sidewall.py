"""Pure decision rule for a side-wall impact trajectory."""

from __future__ import annotations

import math


def evaluate_wall_shot(max_signed_center_m: float, center_limit_m: float,
                       penetration_tolerance_m: float = 0.002,
                       reach_margin_m: float = 0.010) -> dict:
    """Require the probe to reach the wall without crossing its allowed envelope."""
    values = (max_signed_center_m, center_limit_m, penetration_tolerance_m, reach_margin_m)
    if not all(math.isfinite(value) for value in values):
        return {"verdict": "indeterminate", "blocked": False, "reached_wall": False,
                "reason": "a non-finite value prevents classification"}
    overshoot = max_signed_center_m - center_limit_m
    blocked = overshoot <= penetration_tolerance_m
    reached = max_signed_center_m >= center_limit_m - reach_margin_m
    return {
        "verdict": "pass" if blocked and reached else "fail",
        "blocked": blocked,
        "reached_wall": reached,
        "overshoot_m": overshoot,
        "reason": (f"max signed centre {max_signed_center_m:.9f} m; geometric limit "
                   f"{center_limit_m:.9f} m; overshoot {overshoot:.9f} m"),
    }
