"""The probe-outcome decision rule, including the trap it exists to avoid."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.validation.outcome import classify_probe_outcome  # noqa: E402

TOL = {
    "settle_speed_mps": 0.02,
    "rest_local_z_m": 0.002,
    "inside_xy_margin_m": 0.001,
    "fell_through_below_local_z_m": -0.01,
    "at_mouth_min_local_z_m": 0.14,
}
BOX = dict(wall_thickness_m=0.005, probe_size_m=0.04,
           interior_length_m=0.29, interior_width_m=0.19)


def classify(local, speed=0.0, min_z=None):
    return classify_probe_outcome(local, speed, local[2] if min_z is None else min_z,
                                  tolerances=TOL, **BOX)


class TestOutcome(unittest.TestCase):
    def test_probe_on_interior_floor_is_inside(self):
        self.assertEqual(classify([0.0, 0.0, 0.025])["outcome"], "inside")

    def test_probe_on_a_lid_is_at_mouth(self):
        # Resting on a lid whose top is flush with the opening: 0.15 + half probe.
        self.assertEqual(classify([0.0, 0.0, 0.17], min_z=0.17)["outcome"], "at_mouth")

    def test_probe_on_the_world_floor_is_fell_through_not_inside(self):
        """The trap: the box floats 0.20 m up, so the world floor is local z = -0.18.

        In world coordinates this probe is resting on solid ground at z = 0.02 and
        looks perfectly supported. Only the local frame reveals the missing bottom.
        """
        result = classify([0.0, 0.0, -0.18], min_z=-0.18)
        self.assertEqual(result["outcome"], "fell_through")
        self.assertIn("not the box floor", result["reason"])

    def test_still_moving_is_unsettled_not_a_verdict(self):
        self.assertEqual(classify([0.0, 0.0, 0.025], speed=0.5)["outcome"], "unsettled")

    def test_resting_outside_the_cavity_footprint_is_not_inside(self):
        # Correct height, but sitting on a wall top edge far outside the cavity.
        self.assertNotEqual(classify([0.5, 0.0, 0.025])["outcome"], "inside")

    def test_height_between_states_is_indeterminate(self):
        self.assertEqual(classify([0.0, 0.0, 0.08])["outcome"], "indeterminate")

    def test_non_finite_is_indeterminate(self):
        self.assertEqual(classify([0.0, 0.0, float("nan")])["outcome"], "indeterminate")

    def test_evidence_carries_the_numbers_behind_the_label(self):
        ev = classify([0.0, 0.0, 0.025])["evidence"]
        self.assertAlmostEqual(ev["expected_rest_local_z_m"], 0.025, places=9)
        self.assertAlmostEqual(ev["rest_error_m"], 0.0, places=9)
        self.assertTrue(ev["within_interior_xy"])


if __name__ == "__main__":
    unittest.main()
