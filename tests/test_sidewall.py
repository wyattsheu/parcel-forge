import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.validation.sidewall import evaluate_wall_shot  # noqa: E402


class TestSidewallDecision(unittest.TestCase):
    def test_exact_geometric_contact_passes(self):
        self.assertEqual(evaluate_wall_shot(0.125, 0.125)["verdict"], "pass")

    def test_small_solver_penetration_inside_declared_tolerance_passes(self):
        result = evaluate_wall_shot(0.1265, 0.125, penetration_tolerance_m=0.002)
        self.assertEqual(result["verdict"], "pass")
        self.assertAlmostEqual(result["overshoot_m"], 0.0015)

    def test_tunnelling_beyond_tolerance_fails(self):
        result = evaluate_wall_shot(0.130, 0.125, penetration_tolerance_m=0.002)
        self.assertEqual(result["verdict"], "fail")
        self.assertFalse(result["blocked"])

    def test_a_probe_that_never_reaches_the_wall_fails(self):
        result = evaluate_wall_shot(0.050, 0.125, reach_margin_m=0.010)
        self.assertEqual(result["verdict"], "fail")
        self.assertFalse(result["reached_wall"])

    def test_non_finite_evidence_is_indeterminate(self):
        self.assertEqual(evaluate_wall_shot(float("nan"), 0.125)["verdict"], "indeterminate")


if __name__ == "__main__":
    unittest.main()
