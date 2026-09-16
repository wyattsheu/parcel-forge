"""NVIDIA's own USD asset validator, run against our output.

The handbook's section 3 table points at NVIDIA USD Content Agents, whose
workflow has a validation / SimReady entry point. That project's services are not
installable here (and the table says not to assume they are), but the validator
itself ships inside this Isaac Sim install:

    isaacsim/extscache/omni.asset_validator.core-1.19.3/pip_prebundle/usd_validation_nvidia

It imports without Kit, so it joins the fast pxr-only path (D008).

Two rules of use, both from the handbook:
  * our internal G1 rules and these official rules are reported as SEPARATE
    coverage. Passing ours is not a SimReady certification, and this module does
    not claim one either: it reports the rule set and version that actually ran.
  * G7: a validator that cannot fail proves nothing. `self_test()` runs the
    official engine against a deliberately broken fixture and fails the run if
    the engine reports it clean.
"""

from __future__ import annotations

import glob
import os
import sys

PASS, FAIL, WARN, BLOCKED = "pass", "fail", "warn", "blocked"


def _prebundle_path() -> str | None:
    """Locate the vendored validator without hard-coding its version."""
    for base in sys.path:
        if not base or not os.path.isdir(base):
            continue
        hits = glob.glob(os.path.join(base, "isaacsim", "extscache",
                                      "omni.asset_validator.core-*", "pip_prebundle"))
        if hits:
            return sorted(hits)[-1]
    return None


def load_engine():
    """Return (module, version, error). Never raises: a missing validator is `blocked`."""
    path = _prebundle_path()
    if path and path not in sys.path:
        sys.path.insert(0, path)
    try:
        import usd_validation_nvidia as validator
    except Exception as exc:
        return None, None, f"{exc.__class__.__name__}: {exc}"
    version = "unknown"
    if path:
        # .../omni.asset_validator.core-1.19.3/pip_prebundle
        version = os.path.basename(os.path.dirname(path)).split("-", 1)[-1]
    return validator, version, None


def _issue_dict(issue) -> dict:
    severity = getattr(issue.severity, "name", str(issue.severity))
    return {
        "severity": severity,
        "rule": getattr(issue.rule, "__name__", str(issue.rule)),
        "message": str(issue.message),
        "at": str(issue.at) if issue.at is not None else None,
        "suggestion": str(issue.suggestion) if issue.suggestion else None,
    }


def run_official_validation(usd_path: str) -> dict:
    """Run the official engine and report every issue plus the rule set that ran."""
    validator, version, error = load_engine()
    if validator is None:
        return {
            "status": BLOCKED,
            "reason": f"NVIDIA asset validator not importable: {error}",
            "coverage": "official rules did NOT run; this is not a pass",
        }

    engine = validator.ValidationEngine()
    rules = sorted(getattr(r, "__name__", str(r)) for r in engine.rules)
    issues = [_issue_dict(i) for i in engine.validate(usd_path)]
    failures = [i for i in issues if i["severity"] == "FAILURE"]
    warnings = [i for i in issues if i["severity"] == "WARNING"]

    return {
        "status": PASS if not failures else FAIL,
        "validator": "omni.asset_validator (usd_validation_nvidia)",
        "validator_version": version,
        "rules_run_count": len(rules),
        "rules_run": rules,
        "issue_count": len(issues),
        "failures": failures,
        "warnings": warnings,
        "issues": issues,
        "coverage": "NVIDIA's generic USD rule set. It says nothing about whether this box "
                    "can hold an object: cavity containment is proven by the S2 drop test, "
                    "not by a clean validator report.",
        "simready": "not claimed: no SimReady profile was requested or evaluated",
    }


BROKEN_FIXTURE = """#usda 1.0
(
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Xform "A"
{
    def Cube "plate" (
        prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsRigidBodyAPI"]
    )
    {
        double size = 1
        def Cube "nested" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI"]
        )
        {
            double size = 1
        }
    }
}
"""


def self_test(tmp_dir: str) -> dict:
    """G7: prove the official validator can still fail.

    Writes an asset with no defaultPrim and a Gprim nested inside a Gprim, then
    requires the engine to report at least one FAILURE. If this passes clean, the
    engine is not actually checking anything and its verdict on our real asset is
    worthless.
    """
    validator, version, error = load_engine()
    if validator is None:
        return {"status": BLOCKED, "reason": error}

    path = os.path.join(tmp_dir, "validator_self_test_broken.usda")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(BROKEN_FIXTURE)

    issues = [_issue_dict(i) for i in validator.ValidationEngine().validate(path)]
    failures = [i for i in issues if i["severity"] == "FAILURE"]
    return {
        "status": PASS if failures else FAIL,
        "detail": (f"the official engine reported {len(failures)} failure(s) on a deliberately "
                   f"broken asset: {', '.join(sorted({f['rule'] for f in failures}))}")
        if failures else
        "the official engine found NOTHING wrong with a deliberately broken asset; "
        "its verdict on real assets cannot be trusted",
        "fixture": os.path.basename(path),
        "failures": failures,
    }
