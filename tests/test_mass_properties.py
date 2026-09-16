"""Mass, COM and inertia against the handbook's independently computed table.

IsaacSim_Asset_Workflow_Handbook.md section 19 lists values computed outside this
codebase. If these tests ever need loosening, the generator changed, not the maths.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.geometry import plates  # noqa: E402
from parcel_forge.mass_properties import (DERIVED_EXACT, ESTIMATED,  # noqa: E402
                                          center_of_mass, inertia_tensor_about,
                                          is_physically_feasible, mass_manifest,
                                          plate_masses, shell_density)

DEMO = ([0.30, 0.20, 0.15], 0.005)
SHELL_MASS = 0.20


class TestHandbookSection19(unittest.TestCase):
    """The numbers the handbook computed independently, to its stated precision."""

    def setUp(self):
        self.manifest = mass_manifest(*DEMO, SHELL_MASS)
        self.by_name = {p["name"]: p["mass_kg"] for p in self.manifest["plates"]}

    def test_total_plate_volume(self):
        self.assertAlmostEqual(self.manifest["plate_volume_m3"], 0.0010105, places=10)

    def test_bottom_mass(self):
        self.assertAlmostEqual(self.by_name["bottom"], 0.0593765463, places=10)

    def test_x_wall_masses(self):
        for name in ("wall_x_pos", "wall_x_neg"):
            self.assertAlmostEqual(self.by_name[name], 0.0286986640, places=10, msg=name)

    def test_y_wall_masses(self):
        for name in ("wall_y_pos", "wall_y_neg"):
            self.assertAlmostEqual(self.by_name[name], 0.0416130628, places=10, msg=name)

    def test_masses_sum_to_the_shell_mass(self):
        self.assertAlmostEqual(self.manifest["total_mass_kg"], SHELL_MASS, places=12)

    def test_center_of_mass(self):
        com = self.manifest["center_of_mass_local_m"]
        self.assertAlmostEqual(com[0], 0.0, places=12)
        self.assertAlmostEqual(com[1], 0.0, places=12)
        self.assertAlmostEqual(com[2], 0.0552337952, places=10)

    def test_principal_moments_about_com(self):
        ixx, iyy, izz = self.manifest["principal_moments_kg_m2"]
        self.assertAlmostEqual(ixx, 0.0016619320, places=10)
        self.assertAlmostEqual(iyy, 0.0027588147, places=10)
        self.assertAlmostEqual(izz, 0.0034580587, places=10)

    def test_symmetric_box_has_a_diagonal_tensor(self):
        tensor = self.manifest["inertia_about_com_kg_m2"]
        for i in range(3):
            for j in range(3):
                if i != j:
                    self.assertAlmostEqual(tensor[i][j], 0.0, places=12, msg=f"({i},{j})")


class TestDensityBasis(unittest.TestCase):
    def test_density_uses_plate_volume_not_the_outer_envelope(self):
        """The envelope is 0.009 m^3 against 0.0010105 m^3 of actual board: using it
        would understate density by about 8.9x and wreck every derived quantity."""
        table = plates(*DEMO)
        density = shell_density(table, SHELL_MASS)
        self.assertAlmostEqual(density, SHELL_MASS / 0.0010105, places=6)
        envelope_density = SHELL_MASS / (0.30 * 0.20 * 0.15)
        self.assertGreater(density / envelope_density, 8.0)

    def test_mass_is_proportional_to_plate_volume(self):
        table = plates(*DEMO)
        masses = plate_masses(table, SHELL_MASS)
        volumes = [sx * sy * sz for p in table for sx, sy, sz in [p["size_m"]]]
        ratios = [m / v for m, v in zip(masses, volumes)]
        for r in ratios[1:]:
            self.assertAlmostEqual(r, ratios[0], places=9)

    def test_non_positive_shell_mass_is_rejected(self):
        table = plates(*DEMO)
        for bad in (0.0, -1.0, float("nan")):
            with self.assertRaises(ValueError):
                shell_density(table, bad)


class TestScaling(unittest.TestCase):
    """Sanity relations that hold regardless of the specific numbers."""

    def test_doubling_shell_mass_doubles_inertia_and_leaves_com_alone(self):
        single = mass_manifest(*DEMO, SHELL_MASS)
        double = mass_manifest(*DEMO, SHELL_MASS * 2)
        self.assertAlmostEqual(double["center_of_mass_local_m"][2],
                               single["center_of_mass_local_m"][2], places=12)
        for a, b in zip(double["principal_moments_kg_m2"], single["principal_moments_kg_m2"]):
            self.assertAlmostEqual(a, b * 2, places=12)

    def test_com_sits_below_the_box_mid_height(self):
        """An open box has no lid, so its mass is bottom-heavy: the COM must be
        below H/2 = 0.075 m."""
        com_z = mass_manifest(*DEMO, SHELL_MASS)["center_of_mass_local_m"][2]
        self.assertLess(com_z, 0.075)


class TestFaultCasesStayCoherent(unittest.TestCase):
    def test_missing_bottom_shifts_the_com_upward(self):
        normal = mass_manifest(*DEMO, SHELL_MASS)
        broken = mass_manifest(*DEMO, SHELL_MASS, fault="missing_bottom")
        self.assertGreater(broken["center_of_mass_local_m"][2],
                           normal["center_of_mass_local_m"][2])

    def test_asymmetric_assembly_still_yields_a_feasible_tensor(self):
        broken = mass_manifest(*DEMO, SHELL_MASS, fault="missing_bottom")
        self.assertTrue(broken["feasibility"]["feasible"], broken["feasibility"]["reasons"])


class TestPhysicalFeasibility(unittest.TestCase):
    """Adopted from Scalable Real2Sim: no rigid body can have a tensor that fails."""

    def test_the_demo_box_tensor_is_feasible(self):
        result = mass_manifest(*DEMO, SHELL_MASS)["feasibility"]
        self.assertTrue(result["feasible"], result["reasons"])

    def test_triangle_inequality_violation_is_caught(self):
        # Izz far larger than Ixx + Iyy: impossible for any mass distribution.
        bad = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 5.0]]
        result = is_physically_feasible(bad)
        self.assertFalse(result["feasible"])
        self.assertTrue(any("triangle inequality" in r for r in result["reasons"]))

    def test_negative_moment_is_caught(self):
        bad = [[-1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
        self.assertFalse(is_physically_feasible(bad)["feasible"])

    def test_non_finite_is_caught(self):
        bad = [[float("nan"), 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
        self.assertFalse(is_physically_feasible(bad)["feasible"])

    def test_asymmetric_tensor_is_caught(self):
        bad = [[1.0, 0.5, 0], [0.0, 1.0, 0], [0, 0, 1.0]]
        result = is_physically_feasible(bad)
        self.assertFalse(result["feasible"])
        self.assertTrue(any("not symmetric" in r for r in result["reasons"]))

    def test_a_boundary_case_is_accepted(self):
        """A flat plate sits exactly on the triangle equality; it must pass."""
        self.assertTrue(is_physically_feasible([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 2.0]])["feasible"])


class TestProvenanceHonesty(unittest.TestCase):
    def test_nothing_claims_to_be_measured(self):
        prov = mass_manifest(*DEMO, SHELL_MASS)["provenance"]
        self.assertNotIn("measured", prov.values())

    def test_shell_mass_is_marked_as_an_assumption(self):
        prov = mass_manifest(*DEMO, SHELL_MASS)["provenance"]
        self.assertEqual(prov["shell_mass_kg"], ESTIMATED)
        self.assertEqual(prov["inertia"], DERIVED_EXACT)


class TestOffDiagonalTerms(unittest.TestCase):
    def test_off_diagonals_are_computed_not_assumed_zero(self):
        """Shift the reference point off the COM and the products of inertia must
        appear: a tensor about an arbitrary point is not diagonal."""
        table = plates(*DEMO)
        masses = plate_masses(table, SHELL_MASS)
        tensor = inertia_tensor_about(table, masses, (0.05, 0.03, 0.0))
        self.assertNotAlmostEqual(tensor[0][1], 0.0, places=8)

    def test_com_is_the_point_that_diagonalises_this_symmetric_box(self):
        table = plates(*DEMO)
        masses = plate_masses(table, SHELL_MASS)
        com = center_of_mass(table, masses)
        tensor = inertia_tensor_about(table, masses, com)
        self.assertAlmostEqual(tensor[0][1], 0.0, places=12)


if __name__ == "__main__":
    unittest.main()
