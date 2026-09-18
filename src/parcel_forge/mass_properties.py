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


def _determinant_3x3(matrix: list[list[float]]) -> float:
    return (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
            - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
            + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))



def principal_decomposition(tensor: list[list[float]], tolerance: float = 1e-12
                            ) -> tuple[tuple[float, float, float], list[list[float]]]:
    """Return principal moments and a right-handed principal-axis basis.

    The columns of the returned 3x3 matrix are eigenvectors corresponding to the
    ascending moments. A Jacobi sweep is used because the project deliberately
    keeps this verification path independent of NumPy and the simulator runtime.
    """
    if len(tensor) != 3 or any(len(row) != 3 for row in tensor):
        raise ValueError("inertia tensor must be 3x3")
    scale = max(abs(float(value)) for row in tensor for value in row)
    if not math.isfinite(scale) or scale == 0.0:
        raise ValueError("inertia tensor must contain finite, non-zero values")
    symmetry_limit = tolerance * scale
    if any(abs(float(tensor[i][j]) - float(tensor[j][i])) > symmetry_limit
           for i in range(3) for j in range(3)):
        raise ValueError("inertia tensor must be symmetric")

    matrix = [[0.5 * (float(tensor[i][j]) + float(tensor[j][i])) / scale
               for j in range(3)] for i in range(3)]
    axes = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]

    for _ in range(32):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda ij: abs(matrix[ij[0]][ij[1]]))
        if abs(matrix[p][q]) <= tolerance:
            break
        angle = 0.5 * math.atan2(2.0 * matrix[p][q], matrix[q][q] - matrix[p][p])
        cosine, sine = math.cos(angle), math.sin(angle)

        app, aqq, apq = matrix[p][p], matrix[q][q], matrix[p][q]
        matrix[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
        matrix[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
        matrix[p][q] = matrix[q][p] = 0.0
        for index in range(3):
            if index in (p, q):
                continue
            aip, aiq = matrix[index][p], matrix[index][q]
            matrix[index][p] = matrix[p][index] = cosine * aip - sine * aiq
            matrix[index][q] = matrix[q][index] = sine * aip + cosine * aiq
        for row in range(3):
            vip, viq = axes[row][p], axes[row][q]
            axes[row][p] = cosine * vip - sine * viq
            axes[row][q] = sine * vip + cosine * viq

    ordering = sorted(range(3), key=lambda index: matrix[index][index])
    moments = tuple(matrix[index][index] * scale for index in ordering)
    axes = [[axes[row][index] for index in ordering] for row in range(3)]
    if _determinant_3x3(axes) < 0.0:
        for row in range(3):
            axes[row][2] *= -1.0
    return moments, axes


def rotation_matrix_to_quaternion_wxyz(matrix: list[list[float]]) -> tuple[float, float, float, float]:
    """Convert a right-handed 3x3 rotation matrix to a normalized wxyz quaternion."""
    trace = matrix[0][0] + matrix[1][1] + matrix[2][2]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        quaternion = (0.25 * s,
                      (matrix[2][1] - matrix[1][2]) / s,
                      (matrix[0][2] - matrix[2][0]) / s,
                      (matrix[1][0] - matrix[0][1]) / s)
    else:
        index = max(range(3), key=lambda i: matrix[i][i])
        if index == 0:
            s = math.sqrt(1.0 + matrix[0][0] - matrix[1][1] - matrix[2][2]) * 2.0
            quaternion = ((matrix[2][1] - matrix[1][2]) / s, 0.25 * s,
                          (matrix[0][1] + matrix[1][0]) / s,
                          (matrix[0][2] + matrix[2][0]) / s)
        elif index == 1:
            s = math.sqrt(1.0 + matrix[1][1] - matrix[0][0] - matrix[2][2]) * 2.0
            quaternion = ((matrix[0][2] - matrix[2][0]) / s,
                          (matrix[0][1] + matrix[1][0]) / s, 0.25 * s,
                          (matrix[1][2] + matrix[2][1]) / s)
        else:
            s = math.sqrt(1.0 + matrix[2][2] - matrix[0][0] - matrix[1][1]) * 2.0
            quaternion = ((matrix[1][0] - matrix[0][1]) / s,
                          (matrix[0][2] + matrix[2][0]) / s,
                          (matrix[1][2] + matrix[2][1]) / s, 0.25 * s)
    norm = math.sqrt(sum(value * value for value in quaternion))
    return tuple(value / norm for value in quaternion)


def principal_moments(tensor: list[list[float]], tolerance: float = 1e-12) -> tuple[float, float, float]:
    """Eigenvalues of a real symmetric 3x3 inertia tensor, in ascending order.

    This closed form keeps the pure-standard-library path. It is coordinate-frame
    invariant, unlike reading Ixx/Iyy/Izz from the matrix diagonal.
    """
    if len(tensor) != 3 or any(len(row) != 3 for row in tensor):
        raise ValueError("inertia tensor must be 3x3")
    scale = max(abs(float(value)) for row in tensor for value in row)
    if not math.isfinite(scale) or scale == 0.0:
        raise ValueError("inertia tensor must contain finite, non-zero values")
    symmetry_limit = tolerance * scale
    if any(abs(float(tensor[i][j]) - float(tensor[j][i])) > symmetry_limit
           for i in range(3) for j in range(3)):
        raise ValueError("inertia tensor must be symmetric")

    # Average the two stored halves after the symmetry check, then normalize to
    # make the computation insensitive to kg*m^2 scale.
    a = [[0.5 * (float(tensor[i][j]) + float(tensor[j][i])) / scale
          for j in range(3)] for i in range(3)]
    offdiag_sq = a[0][1] ** 2 + a[0][2] ** 2 + a[1][2] ** 2
    if offdiag_sq <= tolerance * tolerance:
        return tuple(sorted((a[0][0] * scale, a[1][1] * scale, a[2][2] * scale)))

    mean = (a[0][0] + a[1][1] + a[2][2]) / 3.0
    spread_sq = ((a[0][0] - mean) ** 2 + (a[1][1] - mean) ** 2
                 + (a[2][2] - mean) ** 2 + 2.0 * offdiag_sq)
    spread = math.sqrt(spread_sq / 6.0)
    if spread <= tolerance:
        return (mean * scale, mean * scale, mean * scale)
    normalized = [[(a[i][j] - (mean if i == j else 0.0)) / spread
                   for j in range(3)] for i in range(3)]
    cosine = max(-1.0, min(1.0, _determinant_3x3(normalized) / 2.0))
    angle = math.acos(cosine) / 3.0
    largest = mean + 2.0 * spread * math.cos(angle)
    smallest = mean + 2.0 * spread * math.cos(angle + 2.0 * math.pi / 3.0)
    middle = 3.0 * mean - largest - smallest
    return tuple(value * scale for value in sorted((smallest, middle, largest)))


def is_physically_feasible(tensor: list[list[float]], tolerance: float = 1e-12) -> dict:
    """Check inertia about COM using coordinate- and scale-invariant conditions.

    Principal moments must be positive. The covariance of the mass distribution,
    Sigma = 0.5*trace(I)*Identity - I, must be positive semidefinite; in principal
    coordinates this is exactly the three inertia triangle inequalities. Equality
    is allowed for an ideal flat distribution.
    """
    if len(tensor) != 3 or any(len(row) != 3 for row in tensor):
        return {"feasible": False, "reasons": ["tensor must be a 3x3 matrix"]}
    values = [float(value) for row in tensor for value in row]
    if not all(math.isfinite(value) for value in values):
        return {"feasible": False, "reasons": ["tensor contains a non-finite value"]}
    scale = max(abs(value) for value in values)
    if scale == 0.0:
        return {"feasible": False, "reasons": ["tensor is zero"]}

    reasons = []
    symmetry_limit = tolerance * scale
    for i in range(3):
        for j in range(i + 1, 3):
            if abs(float(tensor[i][j]) - float(tensor[j][i])) > symmetry_limit:
                reasons.append(f"tensor is not symmetric at ({i},{j})")
    if reasons:
        return {"feasible": False, "reasons": reasons}

    moments = principal_moments(tensor, tolerance)
    normalized = tuple(moment / scale for moment in moments)
    if normalized[0] <= tolerance:
        reasons.append(f"inertia is not positive definite: smallest principal moment is {moments[0]:.6e}")

    # Eigenvalues of Sigma in the same principal basis. A negative value means
    # one principal inertia exceeds the sum of the other two.
    sigma = (
        0.5 * (moments[1] + moments[2] - moments[0]),
        0.5 * (moments[0] + moments[2] - moments[1]),
        0.5 * (moments[0] + moments[1] - moments[2]),
    )
    if min(value / scale for value in sigma) < -tolerance:
        reasons.append("triangle inequality violated by the principal moments: "
                       f"{moments[0]:.6e}, {moments[1]:.6e}, {moments[2]:.6e}")

    return {
        "feasible": not reasons,
        "reasons": reasons,
        "principal_moments": list(moments),
        "pseudo_inertia_covariance_eigenvalues": list(sigma),
        "relative_tolerance": tolerance,
    }


def mass_manifest(outer_size_m, wall_thickness_m, shell_mass_kg: float,
                  fault: str = "none") -> dict:
    """Everything the authoring step and the validator agree on, before any USD."""
    table = plates(outer_size_m, wall_thickness_m, fault)
    masses = plate_masses(table, shell_mass_kg)
    com = center_of_mass(table, masses)
    tensor = inertia_tensor_about(table, masses, com)
    feasibility = is_physically_feasible(tensor)
    moments, axes = principal_decomposition(tensor)

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
        "principal_moments_kg_m2": list(moments),
        "principal_axes_matrix": axes,
        "principal_axes_quaternion_wxyz": list(rotation_matrix_to_quaternion_wxyz(axes)),
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
