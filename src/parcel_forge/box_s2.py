"""S2 fixed open box + centre-drop probe. Runs INSIDE the Isaac Python runtime.

One script, three cases. The case file chooses the fault; the acceptance profile
chooses the thresholds; neither is edited to make a case pass. The outcome is
judged in the box local frame (see parcel_forge.validation.outcome).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

from parcel_forge import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK
from parcel_forge.geometry import SpecError, geometry_manifest
from parcel_forge.pngio import image_stats, write_rgb_png
from parcel_forge.validation.outcome import classify_probe_outcome

G = 9.81


def _close(runtime) -> None:
    """Close last: SimulationApp.close() terminates the process and never returns."""
    try:
        runtime.close()
    except Exception:
        pass


def parse_args(argv):
    p = argparse.ArgumentParser(description="S2 open-box drop test inside the Isaac runtime")
    p.add_argument("--out", required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--profile", required=True)
    return p.parse_args(argv)


def static_geometry_checks(runtime, authored, geom, box_z, tol_m):
    """Read dimensions back from the authored stage, never from the input spec."""
    checks, readback = [], []
    worst_name, worst_err = None, 0.0

    for plate in authored["plates"]:
        bbox = runtime.world_bbox(plate["path"])
        if bbox is None:
            checks.append({"id": f"S2.geometry.{plate['name']}", "status": "fail",
                           "detail": "no world bound could be computed for this plate"})
            continue
        err = max(abs(bbox["size_m"][i] - plate["intended_size_m"][i]) for i in range(3))
        centre_err = max(
            abs(bbox["center_m"][i] - (plate["intended_center_m"][i] + (box_z if i == 2 else 0.0)))
            for i in range(3)
        )
        readback.append({"name": plate["name"], "world_size_m": bbox["size_m"],
                         "world_center_m": bbox["center_m"],
                         "size_error_m": err, "center_error_m": centre_err})
        if err > worst_err:
            worst_name, worst_err = plate["name"], err

    checks.append({
        "id": "S2.plate_dimensions_match_spec",
        "status": "pass" if worst_err <= tol_m else "fail",
        "detail": f"largest world-size error {worst_err:.8f} m"
                  + (f" on {worst_name}" if worst_name else "")
                  + f" (tolerance {tol_m} m), read back through the composed transform",
    })

    expected_plates = geom["plate_count"]
    checks.append({
        "id": "S2.plate_count",
        "status": "pass" if len(authored["plates"]) == expected_plates else "fail",
        "detail": f"{len(authored['plates'])} colliders authored, spec says {expected_plates}",
    })
    checks.append({
        "id": "S2.no_rigid_body_on_fixed_box",
        "status": "pass" if not authored["rigid_body_on_root"] else "fail",
        "detail": "the S2 box is static: no RigidBodyAPI on the root, five separate box "
                  "colliders instead of one convex hull",
    })
    return checks, readback


def main(argv) -> int:
    args = parse_args(argv)
    out = args.out
    os.makedirs(os.path.join(out, "renders"), exist_ok=True)
    with open(args.case, encoding="utf-8") as fh:
        case = json.load(fh)
    with open(args.profile, encoding="utf-8") as fh:
        profile = json.load(fh)

    sim_cfg, tol = profile["simulation"], profile["tolerances"]
    scene_cfg, cam_cfg = profile["scene"], profile["render"]
    g_cfg, probe_cfg = case["geometry"], case["probe"]

    result = {
        "schema": "parcel_forge.s2_result/1",
        "case_id": case["case_id"],
        "fault": g_cfg["fault"],
        "expected_outcome": case["expected_outcome"],
        "profile": os.path.basename(args.profile),
        "runtime": None,
        "geometry": None,
        "physics": {"status": "not_run"},
        "outcome": None,
        "render": {"status": "not_run"},
        "checks": [],
        "errors": [],
    }

    try:
        geom = geometry_manifest(g_cfg["outer_size_m"], g_cfg["wall_thickness_m"], g_cfg["fault"])
    except SpecError as exc:
        result["errors"].append(str(exc))
        result["checks"].append({"id": "S2.spec_valid", "status": "fail", "detail": str(exc)})
        with open(os.path.join(out, "s2_result.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"[S2] spec rejected before launching the simulator: {exc}", flush=True)
        return EXIT_ASSET_FAIL

    result["geometry"] = geom
    box_z = float(case["placement"]["box_outer_bottom_above_world_floor_m"])
    probe_size = float(probe_cfg["size_m"])
    opening_world_z = box_z + geom["outer_size_m"][2]
    probe_spawn = [probe_cfg["drop_xy_m"][0], probe_cfg["drop_xy_m"][1],
                   opening_world_z + float(probe_cfg["drop_offset_above_opening_m"]) + probe_size / 2.0]

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

    runtime = IsaacSimRuntime(dt=sim_cfg["dt"], device=sim_cfg["device"],
                              headless=True, enable_cameras=True)
    try:
        result["runtime"] = runtime.start()
        result["runtime"]["physics_scene"] = runtime.configure_physics(gravity=-G)

        # Physics collider stays large; the visible slab is sized off the box
        # itself, or a 20 m ground plane swallows a 30 cm box in any viewer that
        # auto-frames on world-space bounds (this is what the human WebRTC viewer
        # showed as a full-screen grey wall).
        visual_ground = max(geom["outer_size_m"][0], geom["outer_size_m"][1]) * 4.0
        runtime.add_ground_plane(size=scene_cfg["ground_size_m"], z=0.0, visual_size=visual_ground)
        runtime.add_dome_light(intensity=scene_cfg["dome_light_intensity"])
        runtime.add_distant_light(intensity=scene_cfg["distant_light_intensity"])
        authored = runtime.add_static_box_group("/World/Box", (0.0, 0.0, box_z), geom["plates"])
        probe = runtime.add_rigid_cube("/World/Probe", probe_size, tuple(probe_spawn),
                                       float(probe_cfg["mass_kg"]))
        result["scene"] = {"box": authored, "probe": probe,
                           "box_outer_bottom_world_z_m": box_z,
                           "opening_world_z_m": opening_world_z}

        geo_checks, readback = static_geometry_checks(runtime, authored, geom, box_z, tol["geometry_m"])
        result["checks"].extend(geo_checks)
        result["geometry_readback"] = readback

        asset_path = os.path.join(out, "asset.usda")
        runtime.export_stage(asset_path)
        result["asset"] = {"path": "asset.usda", "note": "flattened stage as simulated"}

        runtime.play()
        view = runtime.rigid_view("/World/Probe")

        traj_path = os.path.join(out, "trajectory.csv")
        min_local_z = float("inf")
        nonfinite_step = None
        rows = []
        with open(traj_path, "w", encoding="utf-8") as fh:
            fh.write("step,sim_time_s,px_m,py_m,pz_m,qw,qx,qy,qz,"
                     "vx_mps,vy_mps,vz_mps,wx_radps,wy_radps,wz_radps,"
                     "local_x_m,local_y_m,local_z_m\n")
            for step in range(1, sim_cfg["steps"] + 1):
                runtime.step(steps=1)
                state = runtime.read_state(view)
                t = runtime.sim_time
                if nonfinite_step is None and not runtime.is_finite(state):
                    nonfinite_step = step
                local = runtime.world_to_local("/World/Box", state["position_m"])
                if math.isfinite(local[2]):
                    min_local_z = min(min_local_z, local[2])
                p, q = state["position_m"], state["orientation_wxyz"]
                v, w = state["linear_velocity_mps"], state["angular_velocity_radps"]
                fh.write(",".join([str(step), f"{t:.6f}"]
                                  + [f"{x:.9f}" for x in (*p, *q, *v, *w, *local)]) + "\n")
                rows.append({"step": step, "t": t, "p": p, "q": q, "v": v, "local": local})

        final = rows[-1]
        speed = math.sqrt(sum(v * v for v in final["v"]))
        result["physics"] = {
            "status": "ran",
            "steps_requested": sim_cfg["steps"],
            "steps_executed": len(rows),
            "dt_s": result["runtime"]["physics_scene"]["dt_readback"],
            "sim_time_end_s": final["t"],
            "final_world_position_m": final["p"],
            "final_box_local_position_m": final["local"],
            "final_speed_mps": speed,
            "min_box_local_z_m": min_local_z,
            "trajectory_csv": "trajectory.csv",
        }

        result["checks"].append({
            "id": "S2.no_nan",
            "status": "pass" if nonfinite_step is None else "fail",
            "detail": "all probe samples finite" if nonfinite_step is None
                      else f"non-finite state first seen at step {nonfinite_step}",
        })
        result["checks"].append({
            "id": "S2.finite_steps",
            "status": "pass" if len(rows) == sim_cfg["steps"] else "fail",
            "detail": f"executed {len(rows)}/{sim_cfg['steps']} steps, ended at t={final['t']:.4f}s",
        })

        verdict = classify_probe_outcome(
            final["local"], speed, min_local_z,
            wall_thickness_m=geom["wall_thickness_m"], probe_size_m=probe_size,
            interior_length_m=geom["interior_length_m"], interior_width_m=geom["interior_width_m"],
            tolerances=tol,
        )
        verdict["judged_in"] = "box local frame (origin = outer bottom face centre)"
        verdict["world_final_z_m"] = final["p"][2]
        result["outcome"] = verdict

        matches = verdict["outcome"] == case["expected_outcome"]
        result["checks"].append({
            "id": "S2.outcome_matches_expectation",
            "status": "pass" if matches else "fail",
            "detail": f"expected '{case['expected_outcome']}', observed '{verdict['outcome']}'. "
                      + verdict["reason"],
        })
        # The fault cases exist to be caught. A fault that lands 'inside' is the
        # failure mode this whole stage is designed to detect.
        if case["expected_outcome"] != "inside":
            result["checks"].append({
                "id": "S2.fault_not_silently_accepted",
                "status": "pass" if verdict["outcome"] != "inside" else "fail",
                "detail": f"fault '{g_cfg['fault']}' produced '{verdict['outcome']}'; "
                          "a fault classified as 'inside' would mean the check is blind",
            })

        # --- render (two views; every expected resting place must be visible) ---
        renders, render_failures = [], []
        for view in cam_cfg["views"]:
            eye = [view["eye_offset_m"][0], view["eye_offset_m"][1], box_z + view["eye_offset_m"][2]]
            target = [view["target_offset_m"][0], view["target_offset_m"][1],
                      box_z + view["target_offset_m"][2]]
            cam_path = f"/World/EvidenceCam_{view['name']}"
            camera = runtime.add_camera(cam_path, tuple(eye), tuple(target),
                                        focal_length=cam_cfg["focal_length_mm"])
            try:
                frame = runtime.capture_rgb(cam_path, cam_cfg["width"], cam_cfg["height"],
                                            settle_frames=cam_cfg["settle_frames"])
            except Exception as exc:
                frame = {"ok": False, "reason": f"{exc.__class__.__name__}: {exc}"}
                result["errors"].append(traceback.format_exc())

            entry = {"view": view["name"], "purpose": view["purpose"], "camera": camera}
            if frame.get("ok"):
                png_rel = os.path.join("renders", f"{case['case_id']}_{view['name']}.png")
                png_path = os.path.join(out, png_rel)
                write_rgb_png(png_path, frame["width"], frame["height"], frame["pixels"], 3)
                stats = image_stats(frame["width"], frame["height"], frame["pixels"], 3)
                entry.update({"status": "ok" if not stats["looks_blank"] else "blank",
                              "png": png_rel, "png_bytes": os.path.getsize(png_path),
                              "image_stats": stats})
                if stats["looks_blank"]:
                    render_failures.append(f"{view['name']} is a flat frame")
            else:
                entry.update({"status": "failed", "reason": frame.get("reason")})
                render_failures.append(f"{view['name']}: {frame.get('reason')}")
            renders.append(entry)

        result["render"] = {
            "status": "ok" if not render_failures else "failed",
            "captured_after": "final physics step (no scene rebuild)",
            "views": renders,
            "png": renders[0].get("png") if renders else None,
        }
        result["checks"].append({
            "id": "S2.render_png_not_blank",
            "status": "pass" if not render_failures else "fail",
            "detail": "; ".join(
                f"{r['view']}={r.get('png_bytes', 0)} B mean_r={r.get('image_stats', {}).get('mean_r')}"
                for r in renders) if not render_failures else "; ".join(render_failures),
        })

        # A viewable copy of the VERIFIED END STATE. The evidence PNGs above come
        # from the live simulation; this file exists because PhysX never writes its
        # results back to USD, so any USD-reading viewer would otherwise show the
        # probe frozen at its spawn pose. The pose written here is the measured one
        # from trajectory.csv, not a re-staged guess.
        runtime.set_prim_transform("/World/Probe", final["p"], final["q"])
        final_scene = os.path.join(out, "scene_final.usda")
        runtime.export_stage(final_scene)
        result["scene_final"] = {
            "path": "scene_final.usda",
            "probe_pose_source": "measured final pose from trajectory.csv (last row)",
            "probe_world_position_m": final["p"],
            "probe_orientation_wxyz": final["q"],
            "note": "open this without --physics to see the verified end state; "
                    "asset.usda keeps the pre-simulation spawn pose",
        }

        result["checks"].append({
            "id": "S2.webrtc_human_view", "status": "not_tested",
            "detail": "livestream never enabled; only a human can confirm a WebRTC view",
        })

    except Exception as exc:
        result["errors"].append(traceback.format_exc())
        result["physics"].setdefault("status", "error")
        with open(os.path.join(out, "s2_result.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"[S2] FAILED: {exc.__class__.__name__}: {exc}", flush=True)
        _close(runtime)
        return EXIT_ENV_FAIL

    graded = [c for c in result["checks"] if c["status"] in ("pass", "fail")]
    failed = [c for c in graded if c["status"] == "fail"]
    result["summary"] = {"checks_total": len(result["checks"]), "checks_graded": len(graded),
                         "checks_failed": len(failed),
                         "observed_outcome": result["outcome"]["outcome"],
                         "verdict": "pass" if not failed else "fail"}
    with open(os.path.join(out, "s2_result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    for c in result["checks"]:
        print(f"[S2] {c['status']:<10} {c['id']}: {c['detail']}", flush=True)
    print(f"[S2] case={case['case_id']} expected={case['expected_outcome']} "
          f"observed={result['outcome']['outcome']} verdict={result['summary']['verdict']}", flush=True)

    _close(runtime)
    return EXIT_OK if not failed else EXIT_ASSET_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
