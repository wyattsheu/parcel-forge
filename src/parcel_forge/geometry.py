"""Open-box geometry: the five-plate table and its validation.

Pure mathematics. This module never imports Kit, USD or numpy, so it can be
tested on the plain system Python and reviewed without a simulator.

Authority: IsaacSim_Asset_Workflow_Handbook.md section 7.
  Outer L x W x H with wall thickness t. The asset's local origin is the centre
  of the OUTER BOTTOM FACE, Z up. All sizes below are FULL extents, never
  half-extents, and the five plates share no volume.

      plate        size (x, y, z)        centre (x, y, z)
      bottom       (L,      W,    t)     (0,            0,            t/2)
      wall_x_pos   (t,      W,    H-t)   ((L-t)/2,      0,            (H+t)/2)
      wall_x_neg   (t,      W,    H-t)   (-(L-t)/2,     0,            (H+t)/2)
      wall_y_pos   (L-2t,   t,    H-t)   (0,            (W-t)/2,      (H+t)/2)
      wall_y_neg   (L-2t,   t,    H-t)   (0,            -(W-t)/2,     (H+t)/2)
"""

from __future__ import annotations

import math

# Fault injections used by S2. They are deliberate defects in the generator's
# input, never changes to the validator or the acceptance thresholds.
FAULTS = ("none", "sealed_lid", "missing_bottom")


class SpecError(ValueError):
    """Raised for a specification that cannot be built. Rejected before any simulator runs."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_box_spec(outer_size_m, wall_thickness_m, fault: str = "none") -> list[str]:
    """Return a list of human-readable reasons this spec is unbuildable (empty == valid)."""
    errors: list[str] = []

    if not isinstance(outer_size_m, (list, tuple)) or len(outer_size_m) != 3:
        return ["outer_size_m must be three numbers [L, W, H]"]

    names = ("L", "W", "H")
    for name, value in zip(names, outer_size_m):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{name} must be a number")
        elif not math.isfinite(value):
            errors.append(f"{name} must be finite")
        elif value <= 0:
            errors.append(f"{name} must be > 0 (got {value})")

    t = wall_thickness_m
    if not isinstance(t, (int, float)) or isinstance(t, bool):
        errors.append("wall_thickness_m must be a number")
    elif not math.isfinite(t):
        errors.append("wall_thickness_m must be finite")
    elif t <= 0:
        errors.append(f"wall_thickness_m must be > 0 (got {t})")

    if errors:
        return errors

    length, width, height = (float(v) for v in outer_size_m)
    t = float(t)
    # Constructibility: without these the plates would overlap or invert.
    if length <= 2 * t:
        errors.append(f"L must be > 2*t ({length} <= {2 * t})")
    if width <= 2 * t:
        errors.append(f"W must be > 2*t ({width} <= {2 * t})")
    if height <= t:
        errors.append(f"H must be > t ({height} <= {t})")

    if fault not in FAULTS:
        errors.append(f"unknown fault '{fault}', expected one of {FAULTS}")

    return errors


def interior(outer_size_m, wall_thickness_m) -> dict:
    """Cavity dimensions and the local height of the interior floor."""
    length, width, height = (float(v) for v in outer_size_m)
    t = float(wall_thickness_m)
    return {
        "interior_length_m": length - 2 * t,
        "interior_width_m": width - 2 * t,
        "interior_height_m": height - t,
        "interior_floor_local_z_m": t,
        "opening_local_z_m": height,
    }


def plates(outer_size_m, wall_thickness_m, fault: str = "none") -> list[dict]:
    """The plate table. Raises SpecError for an unbuildable spec."""
    errors = validate_box_spec(outer_size_m, wall_thickness_m, fault)
    if errors:
        raise SpecError(errors)

    length, width, height = (float(v) for v in outer_size_m)
    t = float(wall_thickness_m)

    table = [
        {"name": "bottom", "size_m": (length, width, t), "center_m": (0.0, 0.0, t / 2)},
        {"name": "wall_x_pos", "size_m": (t, width, height - t),
         "center_m": ((length - t) / 2, 0.0, (height + t) / 2)},
        {"name": "wall_x_neg", "size_m": (t, width, height - t),
         "center_m": (-(length - t) / 2, 0.0, (height + t) / 2)},
        {"name": "wall_y_pos", "size_m": (length - 2 * t, t, height - t),
         "center_m": (0.0, (width - t) / 2, (height + t) / 2)},
        {"name": "wall_y_neg", "size_m": (length - 2 * t, t, height - t),
         "center_m": (0.0, -(width - t) / 2, (height + t) / 2)},
    ]

    if fault == "missing_bottom":
        # The cavity loses its floor: a probe should fall through to the world floor.
        table = [p for p in table if p["name"] != "bottom"]
    elif fault == "sealed_lid":
        # A lid closes the opening: a probe should stop at the mouth, never enter.
        # It spans the interior cross-section only, so it shares no volume with the walls.
        table.append({
            "name": "lid",
            "size_m": (length - 2 * t, width - 2 * t, t),
            "center_m": (0.0, 0.0, height - t / 2),
        })

    return table


def plate_volume_m3(table: list[dict]) -> float:
    return sum(sx * sy * sz for p in table for sx, sy, sz in [p["size_m"]])


def expected_probe_rest_local_z(wall_thickness_m: float, probe_size_m: float) -> float:
    """Where a cube probe's centre rests on the interior floor, in box local Z."""
    return float(wall_thickness_m) + float(probe_size_m) / 2.0


def geometry_manifest(outer_size_m, wall_thickness_m, fault: str = "none") -> dict:
    """Everything the builder and the validator agree on, before any USD exists."""
    table = plates(outer_size_m, wall_thickness_m, fault)
    manifest = {
        "schema": "parcel_forge.box_geometry/1",
        "outer_size_m": [float(v) for v in outer_size_m],
        "wall_thickness_m": float(wall_thickness_m),
        "fault": fault,
        "frame": {"origin": "bottom_outer_center", "up_axis": "Z", "units": "m"},
        "plate_count": len(table),
        "plates": [{"name": p["name"], "size_m": list(p["size_m"]), "center_m": list(p["center_m"])}
                   for p in table],
        "plate_volume_m3": plate_volume_m3(table),
    }
    manifest.update(interior(outer_size_m, wall_thickness_m))
    return manifest
