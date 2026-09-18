"""S4 nine-point placement coverage in one isolated headless PhysX scene."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback

from parcel_forge import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK
from parcel_forge.geometry import geometry_manifest
from parcel_forge.pngio import image_stats, write_rgb_png
from parcel_forge.validation.outcome import classify_probe_outcome


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--skip-render", action="store_true")
    return parser.parse_args(argv)


def _close(runtime):
    try:
        runtime.close()
    except Exception:
        pass


def main(argv):
    args = parse_args(argv)
    with open(args.case, encoding="utf-8") as handle:
        case = json.load(handle)
    with open(args.profile, encoding="utf-8") as handle:
        profile = json.load(handle)

    sim_cfg, tol = profile["simulation"], profile["tolerances"]
    scene_cfg, render_cfg = profile["scene"], profile["render"]
    geom_cfg, probe_cfg = case["geometry"], case["probe"]
    geom = geometry_manifest(geom_cfg["outer_size_m"], geom_cfg["wall_thickness_m"], "none")
    probe_size = float(probe_cfg["size_m"])
    box_z = float(case["placement"]["box_outer_bottom_above_world_floor_m"])

    safe_x = geom["interior_length_m"] / 2.0 - probe_size / 2.0 - 0.010
    safe_y = geom["interior_width_m"] / 2.0 - probe_size / 2.0 - 0.010
    offsets = [(x_name, y_name, x, y)
               for y_name, y in (("neg", -safe_y), ("mid", 0.0), ("pos", safe_y))
               for x_name, x in (("neg", -safe_x), ("mid", 0.0), ("pos", safe_x))]

    result = {
        "schema": "parcel_forge.s4_placement_grid/1",
        "case_id": case["case_id"],
        "coverage": {"point_count": 9, "offsets_box_local_m": [
            {"label": f"x_{xn}_y_{yn}", "x": x, "y": y} for xn, yn, x, y in offsets]},
        "runtime": None,
        "physics": {"status": "not_run"},
        "points": [],
        "render": {"status": "not_run"},
        "checks": [],
        "errors": [],
    }

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
    runtime = IsaacSimRuntime(dt=sim_cfg["dt"], device=sim_cfg["device"],
                              headless=True, enable_cameras=True)
    exit_code = EXIT_ENV_FAIL
    try:
        result["runtime"] = runtime.start()
        result["runtime"]["physics_scene"] = runtime.configure_physics(
            gravity=sim_cfg["gravity_mps2"], enable_ccd=True)
        ground_path = runtime.add_ground_plane(
            size=scene_cfg["ground_size_m"], z=0.0, visual_size=2.2)
        runtime.add_dome_light(intensity=scene_cfg["dome_light_intensity"])
        runtime.add_distant_light(intensity=scene_cfg["distant_light_intensity"])

        metadata = {}
        collider_paths = [ground_path]
        spacing_x, spacing_y = 0.55, 0.45
        opening_world_z = box_z + geom["outer_size_m"][2]
        for index, (x_name, y_name, drop_x, drop_y) in enumerate(offsets):
            row, column = divmod(index, 3)
            center_x = (column - 1) * spacing_x
            center_y = (row - 1) * spacing_y
            label = f"x_{x_name}_y_{y_name}"
            box_path = f"/World/Box_{label}"
            probe_path = f"/World/Probe_{label}"
            authored_box = runtime.add_static_box_group(
                box_path, (center_x, center_y, box_z), geom["plates"])
            collider_paths.extend(plate["path"] for plate in authored_box["plates"])
            spawn = (center_x + drop_x, center_y + drop_y,
                     opening_world_z + float(probe_cfg["drop_offset_above_opening_m"]) + probe_size / 2.0)
            runtime.add_rigid_cube(probe_path, probe_size, spawn, float(probe_cfg["mass_kg"]))
            collider_paths.append(probe_path)
            metadata[probe_path] = {
                "label": label, "box_path": box_path, "box_center_xy_m": [center_x, center_y],
                "requested_drop_offset_local_m": [drop_x, drop_y], "spawn_world_m": list(spawn),
                "min_local_z_m": float("inf"), "final": None,
            }

        contact_readback = runtime.configure_contact_settings(
            collider_paths, profile["contact"],
            material_path="/World/PhysicsMaterials/RigidContactBaseline")
        result["contact_settings"] = {
            "requested": profile["contact"],
            "pre_play_composed_usd_readback": contact_readback,
            "claim_scope": "composed USD readback plus behavior; no tensor getter for coefficients",
        }
        contact_ok = all(
            abs(item["contact_offset_m"] - profile["contact"]["contact_offset_m"]) <= 1e-9
            and abs(item["rest_offset_m"] - profile["contact"]["rest_offset_m"]) <= 1e-9
            and item["bound_physics_material"] == contact_readback["material_path"]
            for item in contact_readback["colliders"])
        result["checks"].append({
            "id": "S4.placement_contact_settings_composed_readback",
            "status": "pass" if contact_ok else "fail",
            "detail": f"{len(collider_paths)} colliders use explicit contact/material settings",
        })
        runtime.play()
        view = runtime.rigid_view("/World/Probe_.*")
        view_paths = [str(path) for path in view.paths]
        missing = sorted(set(metadata) - set(view_paths))
        if missing:
            raise RuntimeError(f"RigidPrim wildcard omitted paths: {missing}")

        trajectory_path = os.path.join(args.out, "trajectory.csv")
        nonfinite = None
        with open(trajectory_path, "w", encoding="utf-8") as handle:
            handle.write("step,sim_time_s,label,px_m,py_m,pz_m,vx_mps,vy_mps,vz_mps,local_x_m,local_y_m,local_z_m\n")
            for step in range(1, sim_cfg["steps"] + 1):
                runtime.step()
                positions, _orientations = view.get_world_poses()
                linear, _angular = view.get_velocities()
                positions, linear = positions.numpy(), linear.numpy()
                for index, path in enumerate(view_paths):
                    info = metadata[path]
                    position = [float(value) for value in positions[index]]
                    velocity = [float(value) for value in linear[index]]
                    local = [position[0] - info["box_center_xy_m"][0],
                             position[1] - info["box_center_xy_m"][1],
                             position[2] - box_z]
                    if not all(math.isfinite(value) for value in (*position, *velocity, *local)):
                        nonfinite = nonfinite or {"step": step, "path": path}
                    info["min_local_z_m"] = min(info["min_local_z_m"], local[2])
                    info["final"] = {"position_world_m": position, "velocity_mps": velocity,
                                     "position_box_local_m": local}
                    handle.write(",".join([
                        str(step), f"{runtime.sim_time:.6f}", info["label"],
                        *[f"{value:.9f}" for value in (*position, *velocity, *local)]
                    ]) + "\n")

        for path in view_paths:
            info = metadata[path]
            final = info["final"]
            speed = math.sqrt(sum(value * value for value in final["velocity_mps"]))
            outcome = classify_probe_outcome(
                final["position_box_local_m"], speed, info["min_local_z_m"],
                wall_thickness_m=geom["wall_thickness_m"], probe_size_m=probe_size,
                interior_length_m=geom["interior_length_m"],
                interior_width_m=geom["interior_width_m"], tolerances=tol)
            point = {**info, "probe_path": path, "final_speed_mps": speed, "outcome": outcome}
            result["points"].append(point)
            result["checks"].append({
                "id": f"S4.placement.{info['label']}",
                "status": "pass" if outcome["outcome"] == "inside" else "fail",
                "detail": f"requested local xy={info['requested_drop_offset_local_m']}; "
                          f"observed {outcome['outcome']} at {final['position_box_local_m']}",
            })

        result["checks"].append({
            "id": "S4.placement_all_samples_finite",
            "status": "pass" if nonfinite is None else "fail",
            "detail": "all nine trajectories finite" if nonfinite is None else str(nonfinite),
        })
        result["contact_settings"]["post_play_composed_usd_readback"] = \
            runtime.read_contact_settings(collider_paths, contact_readback["material_path"])
        result["physics"] = {
            "status": "ran", "steps_executed": sim_cfg["steps"],
            "dt_s": result["runtime"]["physics_scene"]["dt_readback"],
            "sim_time_end_s": runtime.sim_time, "trajectory_csv": "trajectory.csv",
        }

        for point in result["points"]:
            runtime.set_prim_transform(point["probe_path"], point["final"]["position_world_m"])
        runtime.export_stage(os.path.join(args.out, "scene_final.usda"))
        failed = [check for check in result["checks"] if check["status"] == "fail"]
        result["summary"] = {"verdict": "pass" if not failed else "fail",
                             "points_inside": sum(point["outcome"]["outcome"] == "inside"
                                                  for point in result["points"]),
                             "points_total": 9, "checks_failed": len(failed)}
        result["render"] = {"status": "not_tested" if args.skip_render else "pending"}
        with open(os.path.join(args.out, "s4_placement_grid.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        if not args.skip_render:
            camera = runtime.add_camera("/World/EvidenceCam", (1.55, -1.75, 2.15),
                                        (0.0, 0.0, box_z + 0.02),
                                        focal_length=render_cfg["focal_length_mm"])
            frame = runtime.capture_rgb("/World/EvidenceCam", render_cfg["width"], render_cfg["height"],
                                        settle_frames=render_cfg["settle_frames"])
            if frame.get("ok"):
                png_rel = "renders/s4_nine_point_grid.png"
                png_path = os.path.join(args.out, png_rel)
                os.makedirs(os.path.dirname(png_path), exist_ok=True)
                write_rgb_png(png_path, frame["width"], frame["height"], frame["pixels"], 3)
                stats = image_stats(frame["width"], frame["height"], frame["pixels"], 3)
                result["render"] = {"status": "ok" if not stats["looks_blank"] else "blank",
                                    "png": png_rel, "png_bytes": os.path.getsize(png_path),
                                    "image_stats": stats, "camera": camera}
            else:
                result["render"] = {"status": "failed", "reason": frame.get("reason")}
        result["checks"].append({
            "id": "S4.placement_webrtc_human_view", "status": "not_tested",
            "detail": "livestream disabled; only a human can confirm a WebRTC view",
        })

        exit_code = EXIT_OK if not failed else EXIT_ASSET_FAIL
    except Exception as exc:
        result["errors"].append({"type": exc.__class__.__name__, "message": str(exc),
                                 "traceback": traceback.format_exc()})
        result["physics"]["status"] = "error"
        result["summary"] = {"verdict": "insufficient_evidence"}
        exit_code = EXIT_ENV_FAIL
    finally:
        with open(os.path.join(args.out, "s4_placement_grid.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        print(json.dumps(result["summary"], indent=2), flush=True)
        _close(runtime)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
