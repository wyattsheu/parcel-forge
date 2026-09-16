"""Mass, centre of mass and inertia for the plate assembly.

Pure mathematics: no Kit, no USD, no numpy. Runs on the plain system Python so the
numbers can be checked without a simulator, and so a disagreement with PhysX is
attributable to one side or the other.

Reference values this module must reproduce are in
IsaacSim_Asset_Workflow_Handbook.md section 19, computed independently of this code.

Honesty rules (see docs/METHODS.md, Scalable Real2Sim):
  * density is derived from PLATE volume, never from the box's outer envelope --
    a cardboard box is mostly air, and using the envelope would be off by ~100x;
  * every quantity carries a confidence tier. Nothing here is `measured`;
  * inertia is the least trustworthy quantity in any pipeline. Published
    identification error with real torque sensors is ~42%, against ~1.3% for mass.
    Agreement between this formula and PhysX proves the tensor survived authoring,
    and says nothing about a real box.
"""

from __future__ import annotations

import math

from .geometry import plates

# What a number is allowed to claim about itself.
DERIVED_EXACT = "derived_exact"        # closed form over a known shape
ESTIMATED = "estimated"                # an assumption, however reasonable
MEASURED = "measured"                  # nothing in this project qualifies
CONFIDENCE_TIERS = (DERIVED_EXACT, ESTIMATED, MEASURED)


def plate_volumes(table: list[dict]) -> list[float]:
    return [sx * sy * sz for p in table for sx, sy, sz in [p["size_m"]]]


def shell_density(table: list[dict], shell_mass_kg: float) -> float:
    """Density over the plate material only, not the box's outer envelope."""
    total = sum(plate_volumes(table))
    if total <= 0:
        raise ValueError("plate volume must be positive")
    if shell_mass_kg <= 0 or not math.isfinite(shell_mass_kg):
        raise ValueError(f"shell mass must be finite and > 0, got {shell_mass_kg}")
    return shell_mass_kg / total


def plate_masses(table: list[dict], shell_mass_kg: float) -> list[float]:
    """Uniform shell: each plate's mass is proportional to its own volume."""
    density = shell_density(table, shell_mass_kg)
    return [v * density for v in plate_volumes(table)]


def center_of_mass(table: list[dict], masses: list[float]) -> tuple[float, float, float]:
    total = sum(masses)
    return tuple(
        sum(m * p["center_m"][axis] for p, m in zip(table, masses)) / total
        for axis in range(3)
    )


def _solid_box_inertia(mass: float, size: tuple[float, float, float]) -> tuple[float, float, float]:
    """Diagonal inertia of a solid box about its own centre. Sizes are FULL extents."""
    a, b, c = (float(v) for v in size)
    return (
        mass * (b * b + c * c) / 12.0,
        mass * (a * a + c * c) / 12.0,
        mass * (a * a + b * b) / 12.0,
    )


def inertia_tensor_about(table: list[dict], masses: list[float],
                         point: tuple[float, float, float]) -> list[list[float]]:
    """Full 3x3 inertia tensor of the assembly about `point`, via parallel axis.

    Off-diagonal terms are computed rather than assumed zero: they are only zero
    for a symmetric arrangement, and a fault case (a missing plate) is not symmetric.
    """
    tensor = [[0.0] * 3 for _ in range(3)]
    for plate, mass in zip(table, masses):
        ixx, iyy, izz = _solid_box_inertia(mass, plate["size_m"])
        dx = plate["center_m"][0] - point[0]
        dy = plate["center_m"][1] - point[1]
        dz = plate["center_m"][2] - point[2]

        tensor[0][0] += ixx + mass * (dy * dy + dz * dz)
        tensor[1][1] += iyy + mass * (dx * dx + dz * dz)
        tensor[2][2] += izz + mass * (dx * dx + dy * dy)
        tensor[0][1] -= mass * dx * dy
        tensor[0][2] -= mass * dx * dz
        tensor[1][2] -= mass * dy * dz

    tensor[1][0] = tensor[0][1]
    tensor[2][0] = tensor[0][2]
    tensor[2][1] = tensor[1][2]
    return tensor


def is_physically_feasible(tensor: list[list[float]], tolerance: float = 1e-12) -> dict:
    """Could any rigid body have this tensor?

    Adopted from Scalable Real2Sim's pseudo-inertia feasibility constraint. Two
    conditions, both cheap and both absolute -- a tensor that fails is a build
    error, not a tolerance question:

      * positive definite (all leading principal minors > 0);
      * the triangle inequalities on the principal moments,
        Ixx + Iyy >= Izz and its permutations. Mass cannot be distributed so as
        to violate these.
    """
    reasons = []

    for row in tensor:
        for value in row:
            if not math.isfinite(value):
                return {"feasible": False, "reasons": ["tensor contains a non-finite value"]}

    for i in range(3):
        for j in range(3):
            if abs(tensor[i][j] - tensor[j][i]) > 1e-9:
                reasons.append(f"tensor is not symmetric at ({i},{j})")

    m1 = tensor[0][0]
    m2 = tensor[0][0] * tensor[1][1] - tensor[0][1] * tensor[1][0]
    m3 = (tensor[0][0] * (tensor[1][1] * tensor[2][2] - tensor[1][2] * tensor[2][1])
          - tensor[0][1] * (tensor[1][0] * tensor[2][2] - tensor[1][2] * tensor[2][0])
          + tensor[0][2] * (tensor[1][0] * tensor[2][1] - tensor[1][1] * tensor[2][0]))
    for name, minor in (("1x1", m1), ("2x2", m2), ("3x3", m3)):
        if minor <= tolerance:
            reasons.append(f"not positive definite: leading {name} minor is {minor:.6e}")

    ixx, iyy, izz = tensor[0][0], tensor[1][1], tensor[2][2]
    for a, b, c, label in ((ixx, iyy, izz, "Ixx + Iyy >= Izz"),
                           (iyy, izz, ixx, "Iyy + Izz >= Ixx"),
                           (izz, ixx, iyy, "Izz + Ixx >= Iyy")):
        if a + b < c - tolerance:
            reasons.append(f"triangle inequality violated: {label} ({a:.6e} + {b:.6e} < {c:.6e})")

    return {"feasible": not reasons, "reasons": reasons}


def mass_manifest(outer_size_m, wall_thickness_m, shell_mass_kg: float,
                  fault: str = "none") -> dict:
    """Everything the authoring step and the validator agree on, before any USD."""
    table = plates(outer_size_m, wall_thickness_m, fault)
    masses = plate_masses(table, shell_mass_kg)
    com = center_of_mass(table, masses)
    tensor = inertia_tensor_about(table, masses, com)
    feasibility = is_physically_feasible(tensor)

    return {
        "schema": "parcel_forge.mass_properties/1",
        "fault": fault,
        "shell_mass_kg": float(shell_mass_kg),
        "plate_volume_m3": sum(plate_volumes(table)),
        "shell_density_kg_m3": shell_density(table, shell_mass_kg),
        "plates": [{"name": p["name"], "mass_kg": m, "volume_m3": v}
                   for p, m, v in zip(table, masses, plate_volumes(table))],
        "total_mass_kg": sum(masses),
        "center_of_mass_local_m": list(com),
        "inertia_about_com_kg_m2": tensor,
        "principal_moments_kg_m2": [tensor[0][0], tensor[1][1], tensor[2][2]],
        "feasibility": feasibility,
        "provenance": {
            "plate_geometry": DERIVED_EXACT,
            "plate_masses": DERIVED_EXACT,
            "center_of_mass": DERIVED_EXACT,
            "inertia": DERIVED_EXACT,
            "shell_mass_kg": ESTIMATED,
            "mass_distribution": ESTIMATED,
            "note": "derived_exact means the closed form is exact FOR THIS SHAPE under "
                    "the uniform-shell assumption. It is not a measurement of any real "
                    "box, and the shell mass it scales is an assumption.",
        },
    }
