"""S1 minimal simulation: ground plane + cube, finite steps, PNG, evidence.

Runs INSIDE the Isaac Python runtime (launched by `scripts/pf smoke`).
It writes raw results only; pass/fail is decided by the checks below and
recorded, never softened. A render failure is reported separately from the
physics result.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

from parcel_forge import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK
from parcel_forge.pngio import image_stats, write_rgb_png

G = 9.81


def parse_args(argv):
    p = argparse.ArgumentParser(description="S1 cube-drop smoke inside the Isaac runtime")
    p.add_argument("--out", required=True, help="run directory (already created by the host CLI)")
    p.add_argument("--profile", required=True, help="path to the acceptance profile JSON")
    return p.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    out = args.out
    os.makedirs(os.path.join(out, "renders"), exist_ok=True)
    with open(args.profile, encoding="utf-8") as fh:
        profile = json.load(fh)

    sim_cfg = profile["simulation"]
    scene_cfg = profile["scene"]
    tol = profile["tolerances"]

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

    runtime = IsaacSimRuntime(dt=sim_cfg["dt"], device=sim_cfg["device"],
                              headless=True, enable_cameras=True)
    result = {
        "schema": "parcel_forge.s1_result/1",
        "profile": os.path.basename(args.profile),
        "runtime": None,
        "physics": {"status": "not_run"},
        "readback": {"status": "not_run"},
        "render": {"status": "not_run"},
        "checks": [],
        "errors": [],
    }

    try:
        result["runtime"] = runtime.start()
        physics_cfg = runtime.configure_physics(gravity=-G)
        result["runtime"]["physics_scene"] = physics_cfg

        runtime.add_ground_plane(size=scene_cfg["ground_size_m"], z=0.0)
        runtime.add_dome_light(intensity=scene_cfg["dome_light_intensity"])
        runtime.add_distant_light(intensity=scene_cfg["distant_light_intensity"])
        cube_info = runtime.add_rigid_cube(
            path="/World/Cube",
            size=scene_cfg["cube_size_m"],
            position=tuple(scene_cfg["cube_spawn_m"]),
            mass=scene_cfg["cube_mass_kg"],
        )
        result["scene"] = {"cube": cube_info, "ground_size_m": scene_cfg["ground_size_m"]}

        runtime.play()
        view = runtime.rigid_view("/World/Cube")

        traj_path = os.path.join(out, "trajectory.csv")
        rows = []
        nonfinite_step = None
        with open(traj_path, "w", encoding="utf-8") as fh:
            fh.write("step,sim_time_s,px_m,py_m,pz_m,qw,qx,qy,qz,"
                     "vx_mps,vy_mps,vz_mps,wx_radps,wy_radps,wz_radps\n")
            for step in range(1, sim_cfg["steps"] + 1):
                runtime.step(steps=1)
                state = runtime.read_state(view)
                t = runtime.sim_time
                if nonfinite_step is None and not runtime.is_finite(state):
                    nonfinite_step = step
                p, q = state["position_m"], state["orientation_wxyz"]
                v, w = state["linear_velocity_mps"], state["angular_velocity_radps"]
                fh.write(",".join([str(step), f"{t:.6f}"] +
                                  [f"{x:.9f}" for x in (*p, *q, *v, *w)]) + "\n")
                rows.append({"step": step, "t": t, "p": p, "v": v, "q": q, "w": w})

        result["physics"] = {
            "status": "ran",
            "steps_requested": sim_cfg["steps"],
            "steps_executed": len(rows),
            "dt_s": physics_cfg["dt_readback"],
            "sim_time_end_s": rows[-1]["t"],
            "terminated": "finite step budget exhausted",
        }
        result["readback"] = {
            "status": "ok",
            "fields": ["position_m", "orientation_wxyz", "linear_velocity_mps", "angular_velocity_radps"],
            "source_api": "isaacsim.core.experimental.prims.RigidPrim (tensor backend)",
            "first_row": rows[0],
            "last_row": rows[-1],
            "trajectory_csv": "trajectory.csv",
        }

        # --- checks ----------------------------------------------------
        checks = result["checks"]

        checks.append({
            "id": "S1.finite_steps",
            "status": "pass" if len(rows) == sim_cfg["steps"] else "fail",
            "detail": f"executed {len(rows)}/{sim_cfg['steps']} steps, ended at t={rows[-1]['t']:.4f}s",
        })
        checks.append({
            "id": "S1.no_nan",
            "status": "pass" if nonfinite_step is None else "fail",
            "detail": "all pose/velocity samples finite" if nonfinite_step is None
                      else f"non-finite state first seen at step {nonfinite_step}",
        })

        # G0 free-fall against the analytic value, before any contact.
        z0 = scene_cfg["cube_spawn_m"][2]
        target_t = tol["free_fall_check_t_s"]
        sample = min(rows, key=lambda r: abs(r["t"] - target_t))
        fallen = z0 - sample["p"][2]
        analytic = 0.5 * G * sample["t"] ** 2
        err = abs(fallen - analytic)
        checks.append({
            "id": "S1.free_fall_matches_analytic",
            "status": "pass" if err <= tol["free_fall_m"] else "fail",
            "detail": f"at t={sample['t']:.4f}s fell {fallen:.5f} m, analytic {analytic:.5f} m, "
                      f"error {err:.5f} m (tolerance {tol['free_fall_m']} m)",
        })

        expected_rest_z = scene_cfg["cube_size_m"] / 2.0
        final = rows[-1]
        rest_err = abs(final["p"][2] - expected_rest_z)
        checks.append({
            "id": "S1.cube_rests_on_ground",
            "status": "pass" if rest_err <= tol["rest_height_m"] else "fail",
            "detail": f"final z={final['p'][2]:.5f} m, expected {expected_rest_z:.5f} m "
                      f"(half edge), error {rest_err:.5f} m (tolerance {tol['rest_height_m']} m)",
        })

        speed = math.sqrt(sum(v * v for v in final["v"]))
        checks.append({
            "id": "S1.settled",
            "status": "pass" if speed <= tol["settle_speed_mps"] else "fail",
            "detail": f"final |v|={speed:.6f} m/s (tolerance {tol['settle_speed_mps']} m/s)",
        })

        did_not_fall_through = final["p"][2] > -tol["rest_height_m"]
        checks.append({
            "id": "S1.no_tunneling",
            "status": "pass" if did_not_fall_through else "fail",
            "detail": f"final z={final['p'][2]:.5f} m is above the ground plane"
                      if did_not_fall_through else "cube passed through the ground plane",
        })

        # --- render (reported separately from physics) -----------------
        cam_cfg = profile["render"]
        camera = runtime.add_camera("/World/EvidenceCam", tuple(cam_cfg["eye_m"]),
                                    tuple(cam_cfg["target_m"]), focal_length=cam_cfg["focal_length_mm"])
        try:
            frame = runtime.capture_rgb("/World/EvidenceCam", cam_cfg["width"], cam_cfg["height"],
                                        settle_frames=cam_cfg["settle_frames"])
        except Exception as exc:
            frame = {"ok": False, "reason": f"{exc.__class__.__name__}: {exc}"}
            result["errors"].append(traceback.format_exc())

        if frame.get("ok"):
            png_rel = os.path.join("renders", "scene_final.png")
            png_path = os.path.join(out, png_rel)
            write_rgb_png(png_path, frame["width"], frame["height"], frame["pixels"], 3)
            stats = image_stats(frame["width"], frame["height"], frame["pixels"], 3)
            result["render"] = {
                "status": "ok" if not stats["looks_blank"] else "blank",
                "png": png_rel,
                "png_bytes": os.path.getsize(png_path),
                "image_stats": stats,
                "camera": camera,
                "captured_after": "final physics step (no scene rebuild)",
                "settle_frames": frame["settle_frames"],
            }
            checks.append({
                "id": "S1.render_png_not_blank",
                "status": "pass" if not stats["looks_blank"] else "fail",
                "detail": f"{frame['width']}x{frame['height']} png, {os.path.getsize(png_path)} bytes, "
                          f"mean_r={stats['mean_r']}, distinct_r={stats['distinct_r']}"
                          + ("" if not stats["looks_blank"] else " -> flat/black frame is a render failure"),
            })
        else:
            result["render"] = {"status": "failed", "reason": frame.get("reason"), "camera": camera}
            checks.append({
                "id": "S1.render_png_not_blank",
                "status": "fail",
                "detail": f"no image captured: {frame.get('reason')}",
            })

        checks.append({
            "id": "S1.webrtc_human_view",
            "status": "not_tested",
            "detail": "this run never enabled livestream; only a human can confirm a WebRTC view",
        })

    except Exception as exc:
        result["errors"].append(traceback.format_exc())
        result["physics"].setdefault("status", "error")
        with open(os.path.join(out, "s1_result.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"[S1] FAILED: {exc.__class__.__name__}: {exc}", flush=True)
        runtime.close()
        return EXIT_ENV_FAIL
    finally:
        try:
            runtime.close()
        except Exception:
            pass

    graded = [c for c in result["checks"] if c["status"] in ("pass", "fail")]
    failed = [c for c in graded if c["status"] == "fail"]
    result["summary"] = {
        "checks_total": len(result["checks"]),
        "checks_graded": len(graded),
        "checks_failed": len(failed),
        "verdict": "pass" if not failed else "fail",
    }
    with open(os.path.join(out, "s1_result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    for c in result["checks"]:
        print(f"[S1] {c['status']:<10} {c['id']}: {c['detail']}", flush=True)
    print(f"[S1] verdict={result['summary']['verdict']}", flush=True)
    return EXIT_OK if not failed else EXIT_ASSET_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
