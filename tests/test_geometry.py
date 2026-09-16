"""Open-box plate table, against the handbook's own numbers.

Section 7 fixes the plate table; section 19 independently computed the total
plate volume of the demo box as 0.0010105 m^3. Both are pinned here so a later
refactor cannot quietly move the geometry.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parcel_forge.geometry import (SpecError, expected_probe_rest_local_z,  # noqa: E402
                                   geometry_manifest, interior, plate_volume_m3,
                                   plates, validate_box_spec)

DEMO = ([0.30, 0.20, 0.15], 0.005)


class TestInterior(unittest.TestCase):
    def test_demo_box_interior_dimensions(self):
        got = interior(*DEMO)
        self.assertAlmostEqual(got["interior_length_m"], 0.29, places=9)
        self.assertAlmostEqual(got["interior_width_m"], 0.19, places=9)
        self.assertAlmostEqual(got["interior_height_m"], 0.145, places=9)
        self.assertAlmostEqual(got["interior_floor_local_z_m"], 0.005, places=9)
        self.assertAlmostEqual(got["opening_local_z_m"], 0.15, places=9)


class TestPlateTable(unittest.TestCase):
    def setUp(self):
        self.table = {p["name"]: p for p in plates(*DEMO)}

    def test_five_plates(self):
        self.assertEqual(len(self.table), 5)
        self.assertEqual(set(self.table), {"bottom", "wall_x_pos", "wall_x_neg",
                                           "wall_y_pos", "wall_y_neg"})

    def test_bottom(self):
        p = self.table["bottom"]
        self.assertEqual(tuple(round(v, 9) for v in p["size_m"]), (0.3, 0.2, 0.005))
        self.assertEqual(tuple(round(v, 9) for v in p["center_m"]), (0.0, 0.0, 0.0025))

    def test_x_walls(self):
        for name, sign in (("wall_x_pos", 1), ("wall_x_neg", -1)):
            p = self.table[name]
            self.assertEqual(tuple(round(v, 9) for v in p["size_m"]), (0.005, 0.2, 0.145))
            self.assertEqual(tuple(round(v, 9) for v in p["center_m"]), (sign * 0.1475, 0.0, 0.0775))

    def test_y_walls(self):
        for name, sign in (("wall_y_pos", 1), ("wall_y_neg", -1)):
            p = self.table[name]
            self.assertEqual(tuple(round(v, 9) for v in p["size_m"]), (0.29, 0.005, 0.145))
            self.assertEqual(tuple(round(v, 9) for v in p["center_m"]), (0.0, sign * 0.0975, 0.0775))

    def test_plates_do_not_overlap_in_volume(self):
        """Sum of plate volumes equals the handbook's independently computed value."""
        self.assertAlmostEqual(plate_volume_m3(list(self.table.values())), 0.0010105, places=10)

    def test_walls_sit_on_top_of_the_bottom_plate(self):
        """Every wall's lower face must meet the bottom plate's upper face at z = t."""
        bottom = self.table["bottom"]
        bottom_top = bottom["center_m"][2] + bottom["size_m"][2] / 2
        for name in ("wall_x_pos", "wall_x_neg", "wall_y_pos", "wall_y_neg"):
            p = self.table[name]
            wall_base = p["center_m"][2] - p["size_m"][2] / 2
            self.assertAlmostEqual(wall_base, bottom_top, places=9, msg=name)

    def test_walls_reach_the_opening(self):
        for name in ("wall_x_pos", "wall_x_neg", "wall_y_pos", "wall_y_neg"):
            p = self.table[name]
            self.assertAlmostEqual(p["center_m"][2] + p["size_m"][2] / 2, 0.15, places=9, msg=name)


class TestFaults(unittest.TestCase):
    def test_missing_bottom_removes_exactly_the_bottom(self):
        table = plates(*DEMO, fault="missing_bottom")
        self.assertEqual(len(table), 4)
        self.assertNotIn("bottom", [p["name"] for p in table])

    def test_sealed_lid_covers_the_opening_without_overlapping_walls(self):
        table = {p["name"]: p for p in plates(*DEMO, fault="sealed_lid")}
        self.assertEqual(len(table), 6)
        lid = table["lid"]
        # Interior cross-section, so it shares no volume with the walls.
        self.assertEqual(tuple(round(v, 9) for v in lid["size_m"]), (0.29, 0.19, 0.005))
        # Its top face is flush with the opening at z = H.
        self.assertAlmostEqual(lid["center_m"][2] + lid["size_m"][2] / 2, 0.15, places=9)
        # Its bottom face is well above where a probe would rest on the interior floor.
        self.assertGreater(lid["center_m"][2] - lid["size_m"][2] / 2,
                           expected_probe_rest_local_z(0.005, 0.04))

    def test_faulted_specs_still_produce_valid_geometry(self):
        for fault in ("sealed_lid", "missing_bottom"):
            self.assertEqual(validate_box_spec(*DEMO, fault=fault), [], fault)


class TestSpecRejection(unittest.TestCase):
    def test_wall_too_thick_for_length_is_rejected(self):
        errors = validate_box_spec([0.008, 0.20, 0.15], 0.005)
        self.assertTrue(any("L must be > 2*t" in e for e in errors), errors)

    def test_wall_too_thick_for_width_is_rejected(self):
        errors = validate_box_spec([0.30, 0.009, 0.15], 0.005)
        self.assertTrue(any("W must be > 2*t" in e for e in errors), errors)

    def test_height_not_above_thickness_is_rejected(self):
        errors = validate_box_spec([0.30, 0.20, 0.005], 0.005)
        self.assertTrue(any("H must be > t" in e for e in errors), errors)

    def test_non_finite_and_negative_values_are_rejected(self):
        self.assertTrue(validate_box_spec([0.30, 0.20, float("nan")], 0.005))
        self.assertTrue(validate_box_spec([0.30, -0.20, 0.15], 0.005))
        self.assertTrue(validate_box_spec([0.30, 0.20, 0.15], 0.0))

    def test_unknown_fault_is_rejected(self):
        self.assertTrue(validate_box_spec(*DEMO, fault="open_the_lid_a_bit"))

    def test_building_an_invalid_spec_raises_before_any_simulator_runs(self):
        with self.assertRaises(SpecError):
            plates([0.30, 0.20, 0.002], 0.005)


class TestProbeRestHeight(unittest.TestCase):
    def test_demo_probe_rest_height(self):
        # 5 mm interior floor + half of the 4 cm probe.
        self.assertAlmostEqual(expected_probe_rest_local_z(0.005, 0.04), 0.025, places=9)

    def test_thicker_wall_raises_the_interior_floor(self):
        self.assertAlmostEqual(expected_probe_rest_local_z(0.02, 0.04), 0.04, places=9)


class TestManifest(unittest.TestCase):
    def test_manifest_is_json_safe_and_complete(self):
        import json
        m = geometry_manifest(*DEMO)
        json.dumps(m)
        self.assertEqual(m["plate_count"], 5)
        self.assertEqual(m["frame"]["origin"], "bottom_outer_center")
        self.assertAlmostEqual(m["plate_volume_m3"], 0.0010105, places=10)


if __name__ == "__main__":
    unittest.main()
