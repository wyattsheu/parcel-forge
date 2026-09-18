"""S4 PhysX tensor-view readback of authored mass properties."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

from parcel_forge import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--profile", required=True)
    return parser.parse_args(argv)


def _max_error(observed, expected):
    return max(abs(float(a) - float(b)) for a, b in zip(observed, expected))


def _close(runtime):
    try:
        runtime.close()
    except Exception:
        pass


def main(argv):
    args = parse_args(argv)
    with open(args.manifest, encoding="utf-8") as handle:
        manifest = json.load(handle)
    with open(args.profile, encoding="utf-8") as handle:
        profile = json.load(handle)

    expected = manifest["mass_properties"]
    tolerance = profile["tolerances"]
    result = {
        "schema": "parcel_forge.s4_mass_readback/1",
        "runtime": None,
        "source_asset": os.path.basename(args.asset),
        "checks": [],
        "readback": {"status": "not_run"},
        "errors": [],
    }

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
    runtime = IsaacSimRuntime(dt=profile["simulation"]["dt"],
                              device=profile["simulation"]["device"],
                              headless=True, enable_cameras=False)
    exit_code = EXIT_ENV_FAIL
    try:
        result["runtime"] = runtime.start()
        result["runtime"]["physics_scene"] = runtime.configure_physics(gravity=0.0)

        from pxr import UsdGeom
        UsdGeom.Xform.Define(runtime.stage, "/World")
        box = UsdGeom.Xform.Define(runtime.stage, "/World/Box")
        if not box.GetPrim().GetReferences().AddReference(os.path.abspath(args.asset)):
            raise RuntimeError("failed to add the dynamic box USD reference")

        runtime.play()
        view = runtime.rigid_view("/World/Box")
        runtime.step(steps=profile["simulation"]["warmup_steps"])

        mass = float(view.get_masses().numpy()[0][0])
        com_positions, com_orientations = view.get_coms()
        com = [float(value) for value in com_positions.numpy()[0]]
        axes = [float(value) for value in com_orientations.numpy()[0]]
        inertia_flat = [float(value) for value in view.get_inertias().numpy()[0]]
        inertia = [inertia_flat[index:index + 3] for index in range(0, 9, 3)]

        expected_axes = expected["principal_axes_quaternion_wxyz"]
        errors = {
            "mass_kg_absolute": abs(mass - expected["total_mass_kg"]),
            "com_m_absolute": _max_error(com, expected["center_of_mass_local_m"]),
            "inertia_kg_m2_absolute": max(
                abs(inertia[i][j] - expected["inertia_about_com_kg_m2"][i][j])
                for i in range(3) for j in range(3)),
            "principal_axes_quaternion_absolute": min(
                _max_error(axes, expected_axes),
                _max_error(axes, [-value for value in expected_axes])),
        }
        result["readback"] = {
            "status": "ran",
            "backend": "PhysX tensor view through isaacsim.core.experimental.prims.RigidPrim",
            "mass_kg": mass,
            "center_of_mass_local_m": com,
            "principal_axes_quaternion_wxyz": axes,
            "inertia_about_com_kg_m2": inertia,
            "absolute_errors": errors,
            "tolerances": tolerance,
            "simulation_time_s": runtime.sim_time,
        }
        for key, value in errors.items():
            limit = tolerance[key]
            result["checks"].append({
                "id": f"S4.physx_{key}",
                "status": "pass" if math.isfinite(value) and value <= limit else "fail",
                "detail": f"absolute error {value:.12g}, tolerance {limit:.12g}",
            })
        result["checks"].append({
            "id": "S4.parameter_claim_scope",
            "status": "pass",
            "detail": "This comparison proves USD-to-PhysX parameter transport only; shell mass and "
                      "uniform mass distribution are estimated, not measurements of a real box.",
        })
        verdict = "pass" if all(check["status"] == "pass" for check in result["checks"]) else "fail"
        result["summary"] = {"verdict": verdict, "failed": sum(
            check["status"] == "fail" for check in result["checks"])}
        exit_code = EXIT_OK if verdict == "pass" else EXIT_ASSET_FAIL
    except Exception as exc:
        result["readback"]["status"] = "error"
        result["errors"].append({"type": exc.__class__.__name__, "message": str(exc),
                                 "traceback": traceback.format_exc()})
        result["summary"] = {"verdict": "insufficient_evidence", "failed": 0}
        exit_code = EXIT_ENV_FAIL
    finally:
        with open(os.path.join(args.out, "s4_mass_readback.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        print(json.dumps(result, indent=2), flush=True)
        _close(runtime)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
