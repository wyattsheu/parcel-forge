"""Classify where a dropped probe ended up, in the BOX LOCAL frame.

Why local frame: in the missing-bottom fault the probe still comes to rest on a
solid surface (the world floor). Judged in world Z it looks "supported" and the
fault would pass. Judged in box local Z it is clearly below the box, which is
the whole point of the check.

Pure Python: no Kit, no USD, so the decision rule is unit-testable offline.
"""

from __future__ import annotations

import math

OUTCOMES = ("inside", "at_mouth", "fell_through", "unsettled", "indeterminate")


def classify_probe_outcome(final_local_m, final_speed_mps, min_local_z_m,
                           wall_thickness_m, probe_size_m, interior_length_m,
                           interior_width_m, tolerances) -> dict:
    """Return the outcome label plus the numbers that produced it.

    `tolerances` needs: settle_speed_mps, rest_local_z_m, inside_xy_margin_m,
    fell_through_below_local_z_m, at_mouth_min_local_z_m.
    """
    x, y, z = (float(v) for v in final_local_m)
    expected_rest_z = float(wall_thickness_m) + float(probe_size_m) / 2.0
    half_x = interior_length_m / 2.0 - probe_size_m / 2.0 + tolerances["inside_xy_margin_m"]
    half_y = interior_width_m / 2.0 - probe_size_m / 2.0 + tolerances["inside_xy_margin_m"]

    evidence = {
        "final_local_m": [x, y, z],
        "final_speed_mps": float(final_speed_mps),
        "min_local_z_m": float(min_local_z_m),
        "expected_rest_local_z_m": expected_rest_z,
        "rest_error_m": abs(z - expected_rest_z),
        "within_interior_xy": abs(x) <= half_x and abs(y) <= half_y,
    }

    if not all(math.isfinite(v) for v in (x, y, z, final_speed_mps)):
        return {"outcome": "indeterminate", "reason": "non-finite state", "evidence": evidence}

    if final_speed_mps > tolerances["settle_speed_mps"]:
        return {
            "outcome": "unsettled",
            "reason": f"probe still moving at {final_speed_mps:.5f} m/s after the step budget "
                      f"(tolerance {tolerances['settle_speed_mps']} m/s)",
            "evidence": evidence,
        }

    if z < tolerances["fell_through_below_local_z_m"]:
        return {
            "outcome": "fell_through",
            "reason": f"probe came to rest at box-local z={z:.5f} m, below the box itself; "
                      "the surface supporting it is not the box floor",
            "evidence": evidence,
        }

    if evidence["rest_error_m"] <= tolerances["rest_local_z_m"] and evidence["within_interior_xy"]:
        return {
            "outcome": "inside",
            "reason": f"probe rests on the interior floor at box-local z={z:.5f} m "
                      f"(expected {expected_rest_z:.5f} m) and inside the cavity footprint",
            "evidence": evidence,
        }

    if z >= tolerances["at_mouth_min_local_z_m"]:
        return {
            "outcome": "at_mouth",
            "reason": f"probe rests at box-local z={z:.5f} m, at or above the opening; "
                      f"it never entered the cavity (lowest local z reached {min_local_z_m:.5f} m)",
            "evidence": evidence,
        }

    return {
        "outcome": "indeterminate",
        "reason": f"probe settled at box-local z={z:.5f} m, which matches no expected "
                  "resting state; investigate geometry and contact settings",
        "evidence": evidence,
    }
