"""Case-file schema: every rejection class, and the ones that must NOT fire.

These run offline on the system Python. The point of the suite is that each
invalid case file on disk is rejected for the reason it claims, and that the
legal case files stay legal.
"""

import copy
import glob
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from parcel_forge.schema import (ENUM_INVALID, MISSING_FIELD, NOT_CONSTRUCTIBLE,  # noqa: E402
                                 NOT_FINITE, OUT_OF_RANGE, SchemaError, TYPE_ERROR,
                                 UNIT_MISMATCH, UNKNOWN_FIELD, load_case, validate_case,
                                 validate_file)

CASES = os.path.join(ROOT, "cases")


def good():
    with open(os.path.join(CASES, "open_box_normal.json"), encoding="utf-8") as fh:
        return json.load(fh)


def codes(doc):
    return {f["code"] for f in validate_case(doc)}


class TestRealCaseFiles(unittest.TestCase):
    def test_every_legal_case_file_validates(self):
        files = glob.glob(os.path.join(CASES, "*.json"))
        self.assertGreaterEqual(len(files), 6)
        for path in files:
            with self.subTest(case=os.path.basename(path)):
                self.assertEqual(validate_file(path), [], os.path.basename(path))

    def test_every_invalid_case_file_is_rejected_for_its_declared_reason(self):
        with open(os.path.join(CASES, "invalid", "expected_errors.json"), encoding="utf-8") as fh:
            expected = json.load(fh)["expected_error_class"]
        self.assertGreaterEqual(len(expected), 5)
        for case_id, want in expected.items():
            with self.subTest(case=case_id):
                got = {f["code"] for f in validate_file(os.path.join(CASES, "invalid", f"{case_id}.json"))}
                self.assertIn(want, got, f"{case_id}: expected {want}, got {sorted(got)}")


class TestRejectionClasses(unittest.TestCase):
    def test_unknown_field_is_rejected_not_ignored(self):
        """A typo must not be silently accepted: that is how a spec stops meaning what it says."""
        doc = good()
        doc["colour"] = "brown"
        self.assertIn(UNKNOWN_FIELD, codes(doc))

    def test_unknown_nested_field_is_rejected(self):
        doc = good()
        doc["geometry"]["wall_thicknes_m"] = 0.005  # missing an 's'
        self.assertIn(UNKNOWN_FIELD, codes(doc))

    def test_missing_field(self):
        doc = good()
        del doc["probe"]
        self.assertIn(MISSING_FIELD, codes(doc))

    def test_non_finite_value(self):
        doc = good()
        doc["geometry"]["outer_size_m"][2] = float("inf")
        self.assertIn(NOT_FINITE, codes(doc))

    def test_zero_and_negative_mass(self):
        for bad in (0.0, -0.05):
            doc = good()
            doc["probe"]["mass_kg"] = bad
            self.assertIn(OUT_OF_RANGE, codes(doc), bad)

    def test_bad_enum(self):
        doc = good()
        doc["geometry"]["fault"] = "open_the_lid_a_bit"
        self.assertIn(ENUM_INVALID, codes(doc))

    def test_non_si_units_are_never_silently_converted(self):
        doc = good()
        doc["units"]["length"] = "cm"
        self.assertIn(UNIT_MISMATCH, codes(doc))

    def test_wall_thicker_than_half_the_length(self):
        doc = good()
        doc["geometry"]["outer_size_m"] = [0.008, 0.20, 0.15]
        self.assertIn(NOT_CONSTRUCTIBLE, codes(doc))

    def test_probe_wider_than_the_cavity(self):
        doc = good()
        doc["probe"]["size_m"] = 0.25
        self.assertIn(NOT_CONSTRUCTIBLE, codes(doc))

    def test_string_where_a_number_belongs(self):
        doc = good()
        doc["geometry"]["wall_thickness_m"] = "5mm"
        self.assertIn(TYPE_ERROR, codes(doc))

    def test_boolean_is_not_a_number(self):
        """True == 1 in Python; the schema must not accept it as a dimension."""
        doc = good()
        doc["probe"]["size_m"] = True
        self.assertIn(TYPE_ERROR, codes(doc))

    def test_dynamic_body_without_a_mass_is_rejected(self):
        doc = good()
        doc["physics"]["body_mode"] = "dynamic"
        self.assertIn(MISSING_FIELD, codes(doc))

    def test_dynamic_body_with_a_mass_is_accepted(self):
        doc = good()
        doc["physics"]["body_mode"] = "dynamic"
        doc["physics"]["shell_mass_kg"] = 0.2
        self.assertEqual(validate_case(doc), [])


class TestNoFalsePositives(unittest.TestCase):
    def test_the_reference_case_is_clean(self):
        self.assertEqual(validate_case(good()), [])

    def test_optional_description_may_be_absent(self):
        doc = good()
        doc.pop("description", None)
        self.assertEqual(validate_case(doc), [])

    def test_a_thicker_but_legal_wall_is_accepted(self):
        doc = good()
        doc["geometry"]["wall_thickness_m"] = 0.02
        self.assertEqual(validate_case(doc), [])


class TestLoader(unittest.TestCase):
    def test_load_case_raises_with_every_finding(self):
        import tempfile
        doc = good()
        doc["colour"] = "brown"
        doc["probe"]["mass_kg"] = -1.0
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh)
            with self.assertRaises(SchemaError) as ctx:
                load_case(path)
        got = {f["code"] for f in ctx.exception.findings}
        self.assertIn(UNKNOWN_FIELD, got)
        self.assertIn(OUT_OF_RANGE, got)

    def test_load_case_returns_the_document_when_valid(self):
        doc = load_case(os.path.join(CASES, "open_box_normal.json"))
        self.assertEqual(doc["case_id"], "open_box_normal")


if __name__ == "__main__":
    unittest.main()
