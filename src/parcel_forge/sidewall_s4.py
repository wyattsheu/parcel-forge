"""S4 four-direction side-wall blocking test."""

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
from parcel_forge.validation.sidewall import evaluate_wall_shot


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
    case = json.load(open(args.case, encoding="utf-8"))
    profile = json.load(open(args.profile, encoding="utf-8"))
    geom_cfg, probe_cfg = case["geometry"], case["probe"]
    geom = geometry_manifest(geom_cfg["outer_size_m"], geom_cfg["wall_thickness_m"], "none")
    probe_size = float(probe_cfg["size_m"])
    box_z = float(case["placement"]["box_outer_bottom_above_world_floor_m"])
    dt = float(profile["simulation"]["dt"])
    steps = 240
    launch_speed = 1.0
    penetration_tolerance = 0.002
    directions = [
        ("x_pos", (1.0, 0.0, 0.0), 0, 1.0),
        ("x_neg", (-1.0, 0.0, 0.0), 0, -1.0),
        ("y_pos", (0.0, 1.0, 0.0), 1, 1.0),
        ("y_neg", (0.0, -1.0, 0.0), 1, -1.0),
    ]
    result = {
        "schema": "parcel_forge.s4_sidewall/1", "runtime": None,
        "physics": {"status": "not_run"}, "shots": [], "checks": [],
        "render": {"status": "not_run"}, "errors": [],
    }

    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
    runtime = IsaacSimRuntime(dt=dt, device=profile["simulation"]["device"],
                              headless=True, enable_cameras=True)
    exit_code = EXIT_ENV_FAIL
    try:
        result["runtime"] = runtime.start()
        result["runtime"]["physics_scene"] = runtime.configure_physics(gravity=0.0, enable_ccd=True)
        ground_path = runtime.add_ground_plane(
            size=profile["scene"]["ground_size_m"], z=0.0, visual_size=2.2)
        runtime.add_dome_light(intensity=profile["scene"]["dome_light_intensity"])
        runtime.add_distant_light(intensity=profile["scene"]["distant_light_intensity"])

        metadata = {}
        collider_paths = [ground_path]
        centers = [(-0.42, -0.32), (0.42, -0.32), (-0.42, 0.32), (0.42, 0.32)]
        for (label, direction, axis, sign), (center_x, center_y) in zip(directions, centers):
            box_path = f"/World/Box_{label}"
            probe_path = f"/World/Probe_{label}"
            authored_box = runtime.add_static_box_group(
                box_path, (center_x, center_y, box_z), geom["plates"])
            collider_paths.extend(plate["path"] for plate in authored_box["plates"])
            spawn = (center_x, center_y, box_z + 0.075)
            runtime.add_rigid_cube(probe_path, probe_size, spawn, float(probe_cfg["mass_kg"]))
            collider_paths.append(probe_path)
            limit = ((geom["interior_length_m"] if axis == 0 else geom["interior_width_m"]) / 2.0
                     - probe_size / 2.0)
            metadata[probe_path] = {
                "label": label, "direction": list(direction), "axis": axis, "sign": sign,
                "box_center_xy_m": [center_x, center_y], "center_limit_m": limit,
                "max_signed_local_m": -math.inf, "final": None,
            }

        requested_contact = profile["contact"]
        contact_readback = runtime.configure_contact_settings(
            collider_paths, requested_contact,
            material_path="/World/PhysicsMaterials/RigidContactBaseline")
        material = contact_readback["material"]
        collider_mismatches = [
            item for item in contact_readback["colliders"]
            if abs(item["contact_offset_m"] - requested_contact["contact_offset_m"]) > 1e-9
            or abs(item["rest_offset_m"] - requested_contact["rest_offset_m"]) > 1e-9
            or item["bound_physics_material"] != contact_readback["material_path"]
        ]
        material_errors = {
            key: abs(material[key] - requested_contact[key])
            for key in ("static_friction", "dynamic_friction", "restitution")
        }
        contact_ok = not collider_mismatches and max(material_errors.values()) <= 1e-7
        result["contact_settings"] = {
            "requested": requested_contact,
            "pre_play_composed_usd_readback": contact_readback,
            "material_absolute_errors": material_errors,
            "collider_mismatches": collider_mismatches,
            "claim_scope": "composed USD readback plus behavior; no tensor-level coefficient getter exists",
        }
        result["checks"].append({
            "id": "S4.contact_settings_composed_readback",
            "status": "pass" if contact_ok else "fail",
            "detail": f"{len(collider_paths)} colliders bound; material errors={material_errors}; "
                      f"collider mismatches={len(collider_mismatches)}",
        })

        runtime.play()
        view = runtime.rigid_view("/World/Probe_.*")
        paths = [str(path) for path in view.paths]
        velocities = [[metadata[path]["direction"][i] * launch_speed for i in range(3)]
                      for path in paths]
        view.set_velocities(linear_velocities=velocities)

        with open(os.path.join(args.out, "trajectory.csv"), "w", encoding="utf-8") as handle:
            handle.write("step,sim_time_s,label,local_x_m,local_y_m,local_z_m,vx_mps,vy_mps,vz_mps\n")
            for step in range(1, steps + 1):
                runtime.step()
                positions, orientations = view.get_world_poses()
                linear, _angular = view.get_velocities()
                positions, orientations, linear = positions.numpy(), orientations.numpy(), linear.numpy()
                for index, path in enumerate(paths):
                    info = metadata[path]
                    position = [float(v) for v in positions[index]]
                    local = [position[0] - info["box_center_xy_m"][0],
                             position[1] - info["box_center_xy_m"][1],
                             position[2] - box_z]
                    velocity = [float(v) for v in linear[index]]
                    signed = info["sign"] * local[info["axis"]]
                    info["max_signed_local_m"] = max(info["max_signed_local_m"], signed)
                    info["final"] = {"world_position_m": position, "local_position_m": local,
                                     "velocity_mps": velocity,
                                     "orientation_wxyz": [float(v) for v in orientations[index]]}
                    handle.write(",".join([str(step), f"{runtime.sim_time:.6f}", info["label"],
                                          *[f"{v:.9f}" for v in (*local, *velocity)]]) + "\n")

        for path in paths:
            info = metadata[path]
            decision = evaluate_wall_shot(
                info["max_signed_local_m"], info["center_limit_m"],
                penetration_tolerance_m=penetration_tolerance, reach_margin_m=0.010)
            blocked, reached = decision["blocked"], decision["reached_wall"]
            shot = {**info, "probe_path": path, "blocked": blocked, "reached_wall": reached,
                    "penetration_tolerance_m": penetration_tolerance,
                    "overshoot_beyond_center_limit_m": decision["overshoot_m"]}
            result["shots"].append(shot)
            result["checks"].append({
                "id": f"S4.sidewall.{info['label']}",
                "status": "pass" if blocked and reached else "fail",
                "detail": f"max signed center={info['max_signed_local_m']:.8f} m, "
                          f"geometric limit={info['center_limit_m']:.8f} m, "
                          f"overshoot={shot['overshoot_beyond_center_limit_m']:.8f} m; "
                          f"reached_wall={reached}, blocked={blocked}",
            })
            runtime.set_prim_transform(path, info["final"]["world_position_m"],
                                       info["final"]["orientation_wxyz"])

        result["contact_settings"]["post_play_composed_usd_readback"] = \
            runtime.read_contact_settings(collider_paths, contact_readback["material_path"])
        result["physics"] = {"status": "ran", "steps_executed": steps, "dt_s": dt,
                             "sim_time_end_s": runtime.sim_time, "launch_speed_mps": launch_speed,
                             "trajectory_csv": "trajectory.csv"}
        physics_failed = [check for check in result["checks"] if check["status"] == "fail"]
        result["summary"] = {"verdict": "pass" if not physics_failed else "fail",
                             "blocked_shots": sum(shot["blocked"] and shot["reached_wall"]
                                                  for shot in result["shots"]),
                             "shots_total": 4, "physics_checks_failed": len(physics_failed),
                             "render_status": "not_run"}
        # Save completed physics before optional export/render work.
        with open(os.path.join(args.out, "s4_sidewall.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        runtime.export_stage(os.path.join(args.out, "scene_final.usda"))

        if args.skip_render:
            result["render"] = {
                "status": "not_tested",
                "reason": "physics-only run requested; scene_final.usda is available for WebRTC",
            }
        else:
            render_cfg = profile["render"]
            camera = runtime.add_camera("/World/EvidenceCam", (1.20, -1.35, 1.45),
                                        (0.0, 0.0, box_z + 0.06),
                                        focal_length=render_cfg["focal_length_mm"])
            frame = runtime.capture_rgb(
                "/World/EvidenceCam", render_cfg["width"], render_cfg["height"],
                settle_frames=render_cfg["settle_frames"])
            if frame.get("ok"):
                png_rel = "renders/s4_sidewall_four_direction.png"
                png_path = os.path.join(args.out, png_rel)
                os.makedirs(os.path.dirname(png_path), exist_ok=True)
                write_rgb_png(png_path, frame["width"], frame["height"], frame["pixels"], 3)
                stats = image_stats(frame["width"], frame["height"], frame["pixels"], 3)
                result["render"] = {
                    "status": "ok" if not stats["looks_blank"] else "blank",
                    "png": png_rel, "png_bytes": os.path.getsize(png_path),
                    "image_stats": stats, "camera": camera,
                }
            else:
                result["render"] = {"status": "failed", "reason": frame.get("reason")}
        result["checks"].append({
            "id": "S4.sidewall_render_not_blank",
            "status": ("not_tested" if args.skip_render else
                       ("pass" if result["render"]["status"] == "ok" else "fail")),
            "detail": f"{result['render']}",
        })
        result["checks"].append({
            "id": "S4.sidewall_webrtc_human_view", "status": "not_tested",
            "detail": "livestream disabled; only a human can confirm WebRTC viewing",
        })
        result["summary"]["render_status"] = result["render"]["status"]
        # Physics and rendering are reported as separate capabilities.
        exit_code = EXIT_OK if result["summary"]["verdict"] == "pass" else EXIT_ASSET_FAIL
    except Exception as exc:
        result["errors"].append({"type": exc.__class__.__name__, "message": str(exc),
                                 "traceback": traceback.format_exc()})
        result["physics"]["status"] = "error"
        result["summary"] = {"verdict": "insufficient_evidence"}
        exit_code = EXIT_ENV_FAIL
    finally:
        json.dump(result, open(os.path.join(args.out, "s4_sidewall.json"), "w", encoding="utf-8"),
                  indent=2)
        print(json.dumps(result["summary"], indent=2), flush=True)
        _close(runtime)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
