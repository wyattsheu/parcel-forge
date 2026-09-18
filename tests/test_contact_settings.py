import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.contact_settings import validate_contact_settings  # noqa: E402


BASELINE = {
    "contact_offset_m": 0.002,
    "rest_offset_m": 0.0,
    "static_friction": 0.6,
    "dynamic_friction": 0.5,
    "restitution": 0.0,
}


class TestContactSettings(unittest.TestCase):
    def test_baseline_is_valid(self):
        self.assertEqual(validate_contact_settings(BASELINE), [])

    def test_contact_offset_cannot_be_below_rest_offset(self):
        bad = dict(BASELINE, contact_offset_m=0.001, rest_offset_m=0.002)
        self.assertIn("contact_offset_m must be >= rest_offset_m",
                      validate_contact_settings(bad))

    def test_dynamic_friction_cannot_exceed_static_in_this_profile(self):
        bad = dict(BASELINE, static_friction=0.4, dynamic_friction=0.5)
        self.assertIn("dynamic_friction must be <= static_friction for this baseline",
                      validate_contact_settings(bad))

    def test_restitution_range_is_checked(self):
        self.assertTrue(validate_contact_settings(dict(BASELINE, restitution=1.1)))

    def test_non_finite_is_rejected(self):
        self.assertTrue(validate_contact_settings(dict(BASELINE, contact_offset_m=float("nan"))))


if __name__ == "__main__":
    unittest.main()
