"""Host side of the S4 nine-point placement coverage run."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_INSUFFICIENT_EVIDENCE, EXIT_OK
from . import envprobe
from .evidence import (REPO_ROOT, build_manifest, environment_snapshot, make_run_dir,
                       sha256_file, utc_now, write_json)
from .runtime.launcher import IsaacLauncher

CASE = os.path.join(REPO_ROOT, "cases", "open_box_normal.json")
PROFILE = os.path.join(REPO_ROOT, "profiles", "open_box_v1.json")
IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "placement_grid_s4.py")


def _summary(run_dir, result, launch, exit_code):
    lines = [
        f"# S4 nine-point placement {os.path.basename(run_dir)}", "",
        f"- UTC: {utc_now()}",
        f"- PhysX exit: {launch['external_exit_code']}",
        f"- parcel-forge exit: {exit_code}",
        f"- Coverage: {(result or {}).get('summary', {}).get('points_inside', 0)}/9 inside", "",
        "## Placement results", "",
        "| point | requested local xy (m) | final local xyz (m) | speed (m/s) | outcome |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for point in (result or {}).get("points", []):
        lines.append(f"| {point['label']} | {point['requested_drop_offset_local_m']} | "
                     f"{point['final']['position_box_local_m']} | {point['final_speed_mps']:.8f} | "
                     f"{point['outcome']['outcome']} |")
    render = (result or {}).get("render", {})
    lines += ["", "## Evidence media", "",
              f"- Offline PNG: {render.get('png', 'not produced')}",
              f"- PNG status: {render.get('status', 'not_tested')}",
              f"- Image statistics: {render.get('image_stats', 'n/a')}",
              "- WebRTC human confirmation: not_tested", "",
              "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for filename in sorted(files):
            lines.append(f"- {os.path.relpath(os.path.join(root, filename), run_dir)}")
    return "\n".join(lines) + "\n"


def main(argv):
    device, timeout = None, 1800
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])

    run_dir = make_run_dir("s4_placement_grid")
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    shutil.copy(CASE, os.path.join(run_dir, "request.json"))
    shutil.copy(PROFILE, os.path.join(run_dir, "profile.json"))

    gpu = envprobe.gpu_info()
    if gpu["status"] == "ok":
        free = max((item["memory_free_mib"] for item in gpu["gpus"]), default=0)
        if free < 8000:
            write_json(os.path.join(run_dir, "blocked.json"), {
                "blocked_utc": utc_now(), "reason": "insufficient free VRAM to start a new Isaac process",
                "max_free_vram_mib": free,
                "policy": "parcel-forge never stops foreign GPU processes or resets shared state",
            })
            print(f"BLOCKED: only {free} MiB free VRAM. Evidence: {run_dir}/blocked.json")
            return EXIT_ENV_FAIL

    launch = IsaacLauncher(device_index=device).run(
        IN_RUNTIME_SCRIPT,
        ["--out", run_dir, "--case", os.path.join(run_dir, "request.json"),
         "--profile", os.path.join(run_dir, "profile.json")]
        + (["--skip-render"] if "--physics-only" in argv else []),
        log_path=os.path.join(run_dir, "logs", "isaac_runtime.log"), timeout=timeout)
    result_path = os.path.join(run_dir, "s4_placement_grid.json")
    result = json.load(open(result_path, encoding="utf-8")) if os.path.isfile(result_path) else None

    log_text = Path(os.path.join(run_dir, "logs", "isaac_runtime.log")).read_text(errors="replace")
    if result is not None:
        disabled = "CCD will be disabled" in log_text
        result["runtime_ccd_observation"] = {
            "scene_attribute_readback": result.get("runtime", {}).get("physics_scene", {}).get("ccd_enabled"),
            "disable_warning_observed": disabled,
            "effective_status": "disabled_by_runtime_warning" if disabled else "not_confirmed_no_disable_warning_observed",
            "evidence": "logs/isaac_runtime.log",
        }
        write_json(result_path, result)

    if result is None:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    elif launch["external_exit_code"] != 0:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    elif result.get("summary", {}).get("verdict") == "pass":
        exit_code = EXIT_OK
    elif result.get("physics", {}).get("status") == "error":
        exit_code = EXIT_ENV_FAIL
    else:
        exit_code = EXIT_ASSET_FAIL

    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir), stage="S4", case="open_box_nine_point",
        profile=os.path.basename(PROFILE), profile_sha256=sha256_file(PROFILE),
        backend="isaacsim-standalone 6.0.1.0", device=launch["cuda_visible_devices"],
        dt=(result or {}).get("physics", {}).get("dt_s"),
        command=launch["command_str"], exit_code=exit_code,
        external_exit_code=launch["external_exit_code"],
        asset_path="scene_final.usda" if os.path.isfile(os.path.join(run_dir, "scene_final.usda")) else None,
        asset_sha256=sha256_file(os.path.join(run_dir, "scene_final.usda")),
        inputs_sha256={"case": sha256_file(CASE), "profile": sha256_file(PROFILE),
                       "runtime_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={"environment": "environment.json", "request": "request.json",
                  "profile": "profile.json", "result": "s4_placement_grid.json" if result else None,
                  "trajectory": "trajectory.csv" if os.path.isfile(os.path.join(run_dir, "trajectory.csv")) else None,
                  "render": (result or {}).get("render", {}).get("png"),
                  "scene_final": "scene_final.usda" if os.path.isfile(os.path.join(run_dir, "scene_final.usda")) else None,
                  "log": "logs/isaac_runtime.log"},
        notes=["nine placements run simultaneously in nine spatially separated copies of the same box",
               "livestream disabled; PNG is machine-checked for blankness but not visually confirmed by the agent"]))
    Path(os.path.join(run_dir, "summary.md")).write_text(_summary(run_dir, result, launch, exit_code))
    print(f"run: {run_dir}")
    print(f"coverage: {(result or {}).get('summary', {}).get('points_inside', 0)}/9 inside")
    print(f"render: {(result or {}).get('render', {}).get('status', 'not_tested')} "
          f"{(result or {}).get('render', {}).get('png', '')}")
    print(f"summary: {run_dir}/summary.md")
    return exit_code
