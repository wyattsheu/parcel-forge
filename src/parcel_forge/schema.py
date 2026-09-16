"""Case-file schema: reject a bad specification before anything expensive runs.

Standard library only, so this runs on the plain system Python with no simulator,
no USD and no GPU. A spec that fails here never reaches the authoring step.

Design rules from the handbook (section 7):
  * type checking alone is not enough: values must be finite, in range, and
    mutually constructible;
  * unknown fields are REJECTED, not ignored. A silently ignored typo is how a
    specification quietly stops meaning what its author thought it meant;
  * every finding carries a machine-readable error class so failures can be
    counted and compared across runs, not just read by a human.
"""

from __future__ import annotations

import json
import math
import os

# Error classes. Stable identifiers: tests and reports depend on these strings.
UNKNOWN_FIELD = "unknown_field"
MISSING_FIELD = "missing_field"
TYPE_ERROR = "type_error"
NOT_FINITE = "value_not_finite"
OUT_OF_RANGE = "value_out_of_range"
ENUM_INVALID = "enum_invalid"
NOT_CONSTRUCTIBLE = "geometry_not_constructible"
UNIT_MISMATCH = "unit_mismatch"
DUPLICATE_NAME = "duplicate_name"
BAD_JSON = "bad_json"

ERROR_CLASSES = (UNKNOWN_FIELD, MISSING_FIELD, TYPE_ERROR, NOT_FINITE, OUT_OF_RANGE,
                 ENUM_INVALID, NOT_CONSTRUCTIBLE, UNIT_MISMATCH, DUPLICATE_NAME, BAD_JSON)

ASSET_TYPES = ("open_box",)
BODY_MODES = ("static", "dynamic")
COLLIDERS = ("compound_boxes",)
LIDS = ("none",)
FAULTS = ("none", "sealed_lid", "missing_bottom")
PROBE_SHAPES = ("cube",)
EXPECTED_OUTCOMES = ("inside", "at_mouth", "fell_through", "spec_rejected")
SCHEMA_VERSIONS = ("parcel_forge.case/1",)


class SchemaError(ValueError):
    def __init__(self, findings: list[dict]):
        self.findings = findings
        super().__init__("; ".join(f"[{f['code']}] {f['path']}: {f['message']}" for f in findings))


def _finding(code: str, path: str, message: str) -> dict:
    return {"code": code, "path": path, "message": message}


def _check_number(value, path, findings, *, minimum=None, exclusive_min=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        findings.append(_finding(TYPE_ERROR, path, f"expected a number, got {type(value).__name__}"))
        return False
    if not math.isfinite(value):
        findings.append(_finding(NOT_FINITE, path, f"value must be finite, got {value}"))
        return False
    if exclusive_min is not None and value <= exclusive_min:
        findings.append(_finding(OUT_OF_RANGE, path, f"must be > {exclusive_min}, got {value}"))
        return False
    if minimum is not None and value < minimum:
        findings.append(_finding(OUT_OF_RANGE, path, f"must be >= {minimum}, got {value}"))
        return False
    if maximum is not None and value > maximum:
        findings.append(_finding(OUT_OF_RANGE, path, f"must be <= {maximum}, got {value}"))
        return False
    return True


def _check_enum(value, allowed, path, findings):
    if value not in allowed:
        findings.append(_finding(ENUM_INVALID, path, f"must be one of {list(allowed)}, got {value!r}"))
        return False
    return True


def _check_keys(doc, path, required, optional, findings):
    """Required keys must exist; unknown keys are an error, never a shrug."""
    if not isinstance(doc, dict):
        findings.append(_finding(TYPE_ERROR, path, f"expected an object, got {type(doc).__name__}"))
        return False
    for key in required:
        if key not in doc:
            findings.append(_finding(MISSING_FIELD, f"{path}.{key}" if path else key, "required field is absent"))
    known = set(required) | set(optional)
    for key in doc:
        if key not in known:
            findings.append(_finding(UNKNOWN_FIELD, f"{path}.{key}" if path else key,
                                     f"field is not part of the schema; known fields: {sorted(known)}"))
    return True


def _check_vec3(value, path, findings, *, exclusive_min=None):
    if not isinstance(value, list) or len(value) != 3:
        findings.append(_finding(TYPE_ERROR, path, "expected a list of exactly three numbers"))
        return False
    ok = True
    for i, v in enumerate(value):
        ok = _check_number(v, f"{path}[{i}]", findings, exclusive_min=exclusive_min) and ok
    return ok


def validate_case(doc) -> list[dict]:
    """Return every finding for this case document. An empty list means valid."""
    findings: list[dict] = []

    if not _check_keys(doc, "", 
                       required=["schema", "case_id", "asset_type", "intended_task", "units",
                                 "frame", "geometry", "physics", "placement", "probe",
                                 "expected_outcome", "provenance", "seed"],
                       optional=["description"], findings=findings):
        return findings

    if "schema" in doc:
        _check_enum(doc["schema"], SCHEMA_VERSIONS, "schema", findings)
    if "case_id" in doc:
        if not isinstance(doc["case_id"], str) or not doc["case_id"]:
            findings.append(_finding(TYPE_ERROR, "case_id", "expected a non-empty string"))
    if "asset_type" in doc:
        _check_enum(doc["asset_type"], ASSET_TYPES, "asset_type", findings)
    if "intended_task" in doc and not isinstance(doc["intended_task"], str):
        findings.append(_finding(TYPE_ERROR, "intended_task", "expected a string"))
    if "expected_outcome" in doc:
        _check_enum(doc["expected_outcome"], EXPECTED_OUTCOMES, "expected_outcome", findings)
    if "seed" in doc and (isinstance(doc["seed"], bool) or not isinstance(doc["seed"], int)):
        findings.append(_finding(TYPE_ERROR, "seed", "expected an integer"))

    # --- units: this project fixes SI; a mismatch is never silently converted ---
    units = doc.get("units")
    if _check_keys(units, "units", ["length", "mass", "time"], [], findings) and isinstance(units, dict):
        for key, expected in (("length", "m"), ("mass", "kg"), ("time", "s")):
            if key in units and units[key] != expected:
                findings.append(_finding(UNIT_MISMATCH, f"units.{key}",
                                         f"this project works in SI only: expected {expected!r}, got {units[key]!r}"))

    frame = doc.get("frame")
    if _check_keys(frame, "frame", ["origin", "up_axis"], [], findings) and isinstance(frame, dict):
        _check_enum(frame.get("origin"), ("bottom_outer_center",), "frame.origin", findings)
        _check_enum(frame.get("up_axis"), ("Z",), "frame.up_axis", findings)

    # --- geometry: type, range and mutual constructibility ---
    geom = doc.get("geometry")
    if _check_keys(geom, "geometry", ["outer_size_m", "wall_thickness_m", "lid", "fault"], [], findings) \
            and isinstance(geom, dict):
        size_ok = "outer_size_m" in geom and _check_vec3(geom["outer_size_m"], "geometry.outer_size_m",
                                                         findings, exclusive_min=0.0)
        t_ok = "wall_thickness_m" in geom and _check_number(geom["wall_thickness_m"],
                                                            "geometry.wall_thickness_m",
                                                            findings, exclusive_min=0.0)
        _check_enum(geom.get("lid"), LIDS, "geometry.lid", findings)
        _check_enum(geom.get("fault"), FAULTS, "geometry.fault", findings)
        if size_ok and t_ok:
            length, width, height = (float(v) for v in geom["outer_size_m"])
            t = float(geom["wall_thickness_m"])
            # Cross-field rule: the plates must actually fit together.
            if length <= 2 * t:
                findings.append(_finding(NOT_CONSTRUCTIBLE, "geometry",
                                         f"L must be > 2*t: {length} <= {2 * t}"))
            if width <= 2 * t:
                findings.append(_finding(NOT_CONSTRUCTIBLE, "geometry",
                                         f"W must be > 2*t: {width} <= {2 * t}"))
            if height <= t:
                findings.append(_finding(NOT_CONSTRUCTIBLE, "geometry",
                                         f"H must be > t: {height} <= {t}"))

    physics = doc.get("physics")
    if _check_keys(physics, "physics", ["body_mode", "collider"], ["shell_mass_kg", "mass_distribution"],
                   findings) and isinstance(physics, dict):
        _check_enum(physics.get("body_mode"), BODY_MODES, "physics.body_mode", findings)
        _check_enum(physics.get("collider"), COLLIDERS, "physics.collider", findings)
        if "shell_mass_kg" in physics:
            _check_number(physics["shell_mass_kg"], "physics.shell_mass_kg", findings, exclusive_min=0.0)
        if physics.get("body_mode") == "dynamic" and "shell_mass_kg" not in physics:
            findings.append(_finding(MISSING_FIELD, "physics.shell_mass_kg",
                                     "a dynamic body needs a mass; it is not guessed for you"))

    placement = doc.get("placement")
    if _check_keys(placement, "placement", ["box_outer_bottom_above_world_floor_m"], [], findings) \
            and isinstance(placement, dict):
        _check_number(placement.get("box_outer_bottom_above_world_floor_m"),
                      "placement.box_outer_bottom_above_world_floor_m", findings, minimum=0.0)

    probe = doc.get("probe")
    if _check_keys(probe, "probe", ["shape", "size_m", "mass_kg", "drop_offset_above_opening_m", "drop_xy_m"],
                   [], findings) and isinstance(probe, dict):
        _check_enum(probe.get("shape"), PROBE_SHAPES, "probe.shape", findings)
        _check_number(probe.get("size_m"), "probe.size_m", findings, exclusive_min=0.0)
        # Mass must be strictly positive: a zero or negative mass is not a physical body.
        _check_number(probe.get("mass_kg"), "probe.mass_kg", findings, exclusive_min=0.0)
        _check_number(probe.get("drop_offset_above_opening_m"),
                      "probe.drop_offset_above_opening_m", findings, minimum=0.0)
        xy = probe.get("drop_xy_m")
        if not isinstance(xy, list) or len(xy) != 2:
            findings.append(_finding(TYPE_ERROR, "probe.drop_xy_m", "expected a list of exactly two numbers"))
        else:
            for i, v in enumerate(xy):
                _check_number(v, f"probe.drop_xy_m[{i}]", findings)

    # Cross-field: the probe has to fit through the opening it is dropped into.
    if isinstance(geom, dict) and isinstance(probe, dict):
        try:
            length, width, _h = (float(v) for v in geom["outer_size_m"])
            t = float(geom["wall_thickness_m"])
            probe_size = float(probe["size_m"])
            if math.isfinite(probe_size) and probe_size > 0:
                if probe_size >= length - 2 * t or probe_size >= width - 2 * t:
                    findings.append(_finding(NOT_CONSTRUCTIBLE, "probe.size_m",
                                             f"probe edge {probe_size} m does not fit the cavity "
                                             f"{length - 2 * t} x {width - 2 * t} m"))
        except (KeyError, TypeError, ValueError):
            pass  # the individual field errors above already describe the problem

    prov = doc.get("provenance")
    if _check_keys(prov, "provenance", ["dimensions"], ["masses", "material", "shell_mass"], findings) \
            and isinstance(prov, dict):
        for key, value in prov.items():
            if not isinstance(value, str):
                findings.append(_finding(TYPE_ERROR, f"provenance.{key}", "expected a string"))

    return findings


def load_case(path: str) -> dict:
    """Load and validate a case file. Raises SchemaError listing every finding."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SchemaError([_finding(BAD_JSON, os.path.basename(path), f"not valid JSON: {exc}")]) from exc

    findings = validate_case(doc)
    if findings:
        raise SchemaError(findings)
    return doc


def validate_file(path: str) -> list[dict]:
    """Findings for a file, without raising. Used by `pf validate`."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except json.JSONDecodeError as exc:
        return [_finding(BAD_JSON, os.path.basename(path), f"not valid JSON: {exc}")]
    return validate_case(doc)
