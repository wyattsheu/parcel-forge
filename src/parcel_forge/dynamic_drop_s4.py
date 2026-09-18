"""S4 dynamic open-box drop and settling test."""

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


def _close(runtime):
    try:
        runtime.close()
    except Exception:
        pass


def _norm(values):
    return math.sqrt(sum(float(value) ** 2 for value in values))


def main(argv):
    args = parse_args(argv)
    manifest = json.load(open(args.manifest, encoding="utf-8"))
    profile = json.load(open(args.profile, encoding="utf-8"))
    sim_cfg, tolerance = profile["simulation"], profile["tolerances"]
    result = {
        "schema": "parcel_forge.s4_dynamic_drop/1",
        "runtime": None, "physics": {"status": "not_run"},
        "contact_settings": None, "checks": [], "errors": [],
        "render": {"status": "not_tested",
                   "reason": "physics-only run; scene_final.usda is exported for WebRTC"},
    }

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
    runtime = IsaacSimRuntime(dt=sim_cfg["dt"], device=sim_cfg["device"],
                              headless=True, enable_cameras=False)
    exit_code = EXIT_ENV_FAIL
    try:
        result["runtime"] = runtime.start()
        result["runtime"]["physics_scene"] = runtime.configure_physics(
            gravity=sim_cfg["gravity_mps2"], enable_ccd=True)

        from pxr import Gf, UsdGeom, UsdPhysics
        UsdGeom.Xform.Define(runtime.stage, "/World")
        root = UsdGeom.Xform.Define(runtime.stage, "/World/Box")
        if not root.GetPrim().GetReferences().AddReference(os.path.abspath(args.asset)):
            raise RuntimeError("failed to reference dynamic box asset")
        UsdGeom.XformCommonAPI(root).SetTranslate(
            Gf.Vec3d(0.0, 0.0, float(sim_cfg["spawn_root_z_m"])))
        ground_path = runtime.add_ground_plane(size=20.0, z=0.0, visual_size=1.2)

        plate_paths = [f"/World/Box/{plate['name']}" for plate in manifest["plates"]]
        collider_paths = [ground_path, *plate_paths]
        readback = runtime.configure_contact_settings(
            collider_paths, profile["contact"],
            material_path="/World/PhysicsMaterials/RigidContactBaseline")
        result["contact_settings"] = {
            "requested": profile["contact"],
            "pre_play_composed_usd_readback": readback,
            "claim_scope": "composed USD readback plus drop behavior; no tensor getter for coefficients",
        }
        contact_ok = (
            all(abs(item["contact_offset_m"] - profile["contact"]["contact_offset_m"]) <= 1e-9
                and abs(item["rest_offset_m"] - profile["contact"]["rest_offset_m"]) <= 1e-9
                and item["bound_physics_material"] == readback["material_path"]
                for item in readback["colliders"])
            and abs(readback["material"]["static_friction"] -
                    profile["contact"]["static_friction"]) <= 1e-7
            and abs(readback["material"]["dynamic_friction"] -
                    profile["contact"]["dynamic_friction"]) <= 1e-7
            and abs(readback["material"]["restitution"] -
                    profile["contact"]["restitution"]) <= 1e-7
        )
        result["checks"].append({
            "id": "S4.dynamic_drop_contact_readback",
            "status": "pass" if contact_ok else "fail",
            "detail": f"{len(collider_paths)} colliders composed-read-back with explicit material",
        })

        rigid = [prim for prim in runtime.stage.Traverse()
                 if prim.HasAPI(UsdPhysics.RigidBodyAPI)]
        colliders = [prim for prim in runtime.stage.Traverse()
                     if prim.HasAPI(UsdPhysics.CollisionAPI)
                     and str(prim.GetPath()).startswith("/World/Box/")]
        structure_ok = len(rigid) == 1 and str(rigid[0].GetPath()) == "/World/Box" and len(colliders) == 5
        result["checks"].append({
            "id": "S4.dynamic_drop_single_body_structure",
            "status": "pass" if structure_ok else "fail",
            "detail": f"rigid bodies={[str(p.GetPath()) for p in rigid]}; "
                      f"box colliders={[str(p.GetPath()) for p in colliders]}",
        })

        runtime.play()
        view = runtime.rigid_view("/World/Box")
        rows = []
        nonfinite_step = None
        trajectory = os.path.join(args.out, "trajectory.csv")
        with open(trajectory, "w", encoding="utf-8") as handle:
            handle.write("step,sim_time_s,px_m,py_m,pz_m,qw,qx,qy,qz,"
                         "vx_mps,vy_mps,vz_mps,wx_radps,wy_radps,wz_radps\n")
            for step in range(1, int(sim_cfg["steps"]) + 1):
                runtime.step()
                state = runtime.read_state(view)
                values = (*state["position_m"], *state["orientation_wxyz"],
                          *state["linear_velocity_mps"], *state["angular_velocity_radps"])
                if nonfinite_step is None and not all(math.isfinite(value) for value in values):
                    nonfinite_step = step
                row = {"step": step, "time_s": runtime.sim_time, **state}
                rows.append(row)
                handle.write(",".join([
                    str(step), f"{runtime.sim_time:.6f}",
                    *[f"{value:.9f}" for value in values],
                ]) + "\n")

        window_steps = max(1, round(float(sim_cfg["settle_window_s"]) / sim_cfg["dt"]))
        window = rows[-window_steps:]
        max_linear = max(_norm(row["linear_velocity_mps"]) for row in window)
        max_angular = max(_norm(row["angular_velocity_radps"]) for row in window)
        final = rows[-1]
        min_z = min(row["position_m"][2] for row in rows)
        fell = final["position_m"][2] < sim_cfg["spawn_root_z_m"] - 0.20
        checks = [
            ("S4.dynamic_drop_finite", nonfinite_step is None,
             "all trajectory samples finite" if nonfinite_step is None
             else f"first non-finite sample at step {nonfinite_step}"),
            ("S4.dynamic_drop_fell", fell,
             f"root z moved from {sim_cfg['spawn_root_z_m']} to {final['position_m'][2]:.9f} m"),
            ("S4.dynamic_drop_no_floor_tunneling", min_z >= tolerance["min_root_z_m"],
             f"minimum root z={min_z:.9f} m; limit={tolerance['min_root_z_m']} m"),
            ("S4.dynamic_drop_final_height", abs(final["position_m"][2]) <=
             tolerance["final_root_z_abs_m"],
             f"final root z={final['position_m'][2]:.9f} m; "
             f"absolute tolerance={tolerance['final_root_z_abs_m']} m"),
            ("S4.dynamic_drop_settled_linear", max_linear <=
             tolerance["settle_linear_speed_mps"],
             f"last {sim_cfg['settle_window_s']} s max linear speed={max_linear:.9g} m/s"),
            ("S4.dynamic_drop_settled_angular", max_angular <=
             tolerance["settle_angular_speed_radps"],
             f"last {sim_cfg['settle_window_s']} s max angular speed={max_angular:.9g} rad/s"),
        ]
        for check_id, passed, detail in checks:
            result["checks"].append({"id": check_id, "status": "pass" if passed else "fail",
                                     "detail": detail})

        result["contact_settings"]["post_play_composed_usd_readback"] = (
            runtime.read_contact_settings(collider_paths, readback["material_path"]))
        result["physics"] = {
            "status": "ran", "steps_executed": len(rows), "dt_s": sim_cfg["dt"],
            "sim_time_end_s": final["time_s"], "spawn_root_z_m": sim_cfg["spawn_root_z_m"],
            "final_state": final, "minimum_root_z_m": min_z,
            "settle_window_s": sim_cfg["settle_window_s"],
            "settle_window_max_linear_speed_mps": max_linear,
            "settle_window_max_angular_speed_radps": max_angular,
            "trajectory_csv": "trajectory.csv",
        }
        runtime.set_prim_transform("/World/Box", final["position_m"], final["orientation_wxyz"])
        runtime.export_stage(os.path.join(args.out, "scene_final.usda"))

        failed = [check for check in result["checks"] if check["status"] == "fail"]
        result["summary"] = {"verdict": "pass" if not failed else "fail",
                             "checks_failed": len(failed),
                             "render_status": "not_tested",
                             "webrtc_human_view": "not_tested"}
        exit_code = EXIT_OK if not failed else EXIT_ASSET_FAIL
    except Exception as exc:
        result["errors"].append({"type": exc.__class__.__name__, "message": str(exc),
                                 "traceback": traceback.format_exc()})
        result["physics"]["status"] = "error"
        result["summary"] = {"verdict": "insufficient_evidence"}
        exit_code = EXIT_ENV_FAIL
    finally:
        json.dump(result, open(os.path.join(args.out, "s4_dynamic_drop.json"),
                               "w", encoding="utf-8"), indent=2)
        print(json.dumps(result["summary"], indent=2), flush=True)
        _close(runtime)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
