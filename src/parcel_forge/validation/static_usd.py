"""G1 static checks on the USD file that was actually written.

The rule that matters: dimensions are read back from the OUTPUT stage through the
composed transform. Comparing the input spec against itself proves nothing, and a
double scale on an ancestor is exactly the bug this is meant to catch.
"""

from __future__ import annotations

import math

PASS, FAIL, BLOCKED = "pass", "fail", "blocked"


def _check(rule_id, status, detail, measured=None):
    return {"rule": rule_id, "status": status, "detail": detail, "measured": measured}


def validate_asset(usd_path: str, expected: dict, tolerance_m: float = 0.0001) -> dict:
    """Reopen `usd_path` and check it against the build manifest `expected`."""
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    checks = []

    stage = Usd.Stage.Open(usd_path)
    if stage is None:
        return {"schema": "parcel_forge.static_validation/1", "asset": usd_path,
                "checks": [_check("G1.stage_opens", FAIL, "the stage could not be opened")],
                "summary": {"verdict": "fail", "failed": 1}}
    checks.append(_check("G1.stage_opens", PASS, "stage opened from the written file"))

    # Unresolved references would make the asset load differently elsewhere.
    unresolved = [str(p.GetPath()) for p in stage.Traverse()
                  if p.GetPrimStack() and not p.IsValid()]
    missing = stage.GetRootLayer().GetCompositionAssetDependencies()
    broken = [a for a in missing if not Usd.Stage.Open(a)] if missing else []
    checks.append(_check(
        "G1.no_missing_references",
        PASS if not unresolved and not broken else FAIL,
        f"{len(missing or [])} external dependency/ies, {len(broken)} unresolvable",
        {"dependencies": list(missing or []), "broken": broken, "invalid_prims": unresolved}))

    default_prim = stage.GetDefaultPrim()
    want_default = expected["default_prim"]
    checks.append(_check(
        "G1.default_prim",
        PASS if default_prim and str(default_prim.GetPath()) == want_default else FAIL,
        f"defaultPrim is {str(default_prim.GetPath()) if default_prim else 'unset'}, expected {want_default}"))

    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    kpu = UsdPhysics.GetStageKilogramsPerUnit(stage)
    up = UsdGeom.GetStageUpAxis(stage)
    checks.append(_check(
        "G1.stage_units_and_axis",
        PASS if (abs(mpu - 1.0) < 1e-12 and abs(kpu - 1.0) < 1e-12 and up == "Z") else FAIL,
        f"metersPerUnit={mpu}, kilogramsPerUnit={kpu}, upAxis={up}; expected 1.0 / 1.0 / Z",
        {"metersPerUnit": mpu, "kilogramsPerUnit": kpu, "upAxis": str(up)}))

    # --- per-plate dimensions, read back from the output geometry ---
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                             [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    worst_err, worst_name, measured = 0.0, None, []
    for plate in expected["authored_prims"]:
        prim = stage.GetPrimAtPath(plate["path"])
        if not prim or not prim.IsValid():
            checks.append(_check(f"G1.plate_present[{plate['name']}]", FAIL, "prim missing from the written file"))
            continue
        box = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        lo, hi = box.GetMin(), box.GetMax()
        size = [float(hi[i] - lo[i]) for i in range(3)]
        centre = [float((hi[i] + lo[i]) / 2.0) for i in range(3)]
        size_err = max(abs(size[i] - plate["size_m"][i]) for i in range(3))
        centre_err = max(abs(centre[i] - plate["center_m"][i]) for i in range(3))
        measured.append({"name": plate["name"], "world_size_m": size, "world_center_m": centre,
                         "size_error_m": size_err, "center_error_m": centre_err})
        if max(size_err, centre_err) > worst_err:
            worst_err, worst_name = max(size_err, centre_err), plate["name"]

    checks.append(_check(
        "G1.plate_dimensions",
        PASS if worst_err <= tolerance_m and measured else FAIL,
        f"largest world size/centre error {worst_err:.10f} m"
        + (f" on {worst_name}" if worst_name else "")
        + f" (tolerance {tolerance_m} m), read back through the composed transform",
        measured))

    colliders = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
    checks.append(_check(
        "G1.collider_count",
        PASS if len(colliders) == expected["plate_count"] else FAIL,
        f"{len(colliders)} colliders, expected {expected['plate_count']}",
        [str(p.GetPath()) for p in colliders]))

    rigid = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    want_rigid = expected["rigid_body_count_expected"]
    checks.append(_check(
        "G1.rigid_body_count",
        PASS if len(rigid) == want_rigid else FAIL,
        f"{len(rigid)} rigid bodies, expected {want_rigid} for body_mode={expected['body_mode']}",
        [str(p.GetPath()) for p in rigid]))

    # A rigid body inside another rigid body is a silent physics bug.
    nested = []
    for prim in rigid:
        parent = prim.GetParent()
        while parent and parent.IsValid() and str(parent.GetPath()) != "/":
            if parent.HasAPI(UsdPhysics.RigidBodyAPI):
                nested.append(f"{prim.GetPath()} inside {parent.GetPath()}")
            parent = parent.GetParent()
    checks.append(_check("G1.no_nested_rigid_bodies", PASS if not nested else FAIL,
                         "no rigid body is nested inside another" if not nested else "; ".join(nested),
                         nested))

    names = [p.GetName() for p in stage.Traverse()]
    dupes = sorted({n for n in names if names.count(n) > 1})
    checks.append(_check("G1.unique_prim_names", PASS if not dupes else FAIL,
                         "all prim names unique" if not dupes else f"duplicated: {dupes}", dupes))

    bad_mass = []
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.MassAPI):
            attr = UsdPhysics.MassAPI(prim).GetMassAttr()
            value = attr.Get() if attr else None
            if value is not None and (not math.isfinite(value) or value <= 0):
                bad_mass.append(f"{prim.GetPath()}={value}")
    checks.append(_check("G1.finite_positive_mass", PASS if not bad_mass else FAIL,
                         "every authored mass is finite and > 0" if not bad_mass else "; ".join(bad_mass),
                         bad_mass))

    # The official NVIDIA rule set is appended by the caller (usd_tool), so that
    # internal and official coverage stay separately identifiable in the report.

    graded = [c for c in checks if c["status"] in (PASS, FAIL)]
    failed = [c for c in graded if c["status"] == FAIL]
    return {
        "schema": "parcel_forge.static_validation/1",
        "asset": usd_path,
        "tolerance_m": tolerance_m,
        "checks": checks,
        "summary": {"total": len(checks), "graded": len(graded), "failed": len(failed),
                    "blocked": len([c for c in checks if c["status"] == BLOCKED]),
                    "verdict": "pass" if not failed else "fail"},
    }
