"""Host side of the S4 four-direction side-wall blocking run."""

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
IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "sidewall_s4.py")


def main(argv):
    device, timeout = None, 1800
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])
    run_dir = make_run_dir("s4_sidewall")
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

    runtime_args = ["--out", run_dir, "--case", os.path.join(run_dir, "request.json"),
                    "--profile", os.path.join(run_dir, "profile.json")]
    if "--physics-only" in argv:
        runtime_args.append("--skip-render")
    launch = IsaacLauncher(device_index=device).run(
        IN_RUNTIME_SCRIPT, runtime_args,
        log_path=os.path.join(run_dir, "logs", "isaac_runtime.log"), timeout=timeout)
    result_path = os.path.join(run_dir, "s4_sidewall.json")
    result = json.load(open(result_path, encoding="utf-8")) if os.path.isfile(result_path) else None
    log_path = os.path.join(run_dir, "logs", "isaac_runtime.log")
    log_text = Path(log_path).read_text(errors="replace") if os.path.isfile(log_path) else ""
    ccd_disable_warning = "CCD will be disabled" in log_text
    if result is not None:
        scene_ccd_attr = result.get("runtime", {}).get("physics_scene", {}).get("ccd_enabled")
        result["runtime_ccd_observation"] = {
            "scene_attribute_readback": scene_ccd_attr,
            "disable_warning_observed": ccd_disable_warning,
            "effective_status": ("disabled_by_runtime_warning" if ccd_disable_warning
                                 else "not_confirmed_no_disable_warning_observed"),
            "evidence": "logs/isaac_runtime.log",
            "claim_scope": "runtime log classification; the USD attribute alone is not effective-state proof",
        }
        result.setdefault("checks", []).append({
            "id": "S4.ccd_effective_runtime_state",
            "status": "warning" if ccd_disable_warning else "unknown",
            "detail": ("scene CCD attribute is true but PhysX logged that CCD will be disabled"
                       if ccd_disable_warning else
                       "no disable warning observed; effective CCD still lacks a tensor getter"),
        })
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)

    if result is None:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    elif result.get("physics", {}).get("status") == "error":
        exit_code = EXIT_ENV_FAIL
    elif result.get("summary", {}).get("verdict") != "pass":
        exit_code = EXIT_ASSET_FAIL
    elif launch["external_exit_code"] != 0:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    else:
        exit_code = EXIT_OK

    scene = os.path.join(run_dir, "scene_final.usda")
    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir), stage="S4", case="open_box_sidewall_four_direction",
        profile=os.path.basename(PROFILE), profile_sha256=sha256_file(PROFILE),
        backend="isaacsim-standalone 6.0.1.0", device=launch["cuda_visible_devices"],
        dt=(result or {}).get("physics", {}).get("dt_s"), command=launch["command_str"],
        exit_code=exit_code, external_exit_code=launch["external_exit_code"],
        asset_path="scene_final.usda" if os.path.isfile(scene) else None,
        asset_sha256=sha256_file(scene),
        inputs_sha256={"case": sha256_file(CASE), "profile": sha256_file(PROFILE),
                       "runtime_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={"environment": "environment.json", "request": "request.json",
                  "profile": "profile.json", "result": "s4_sidewall.json" if result else None,
                  "trajectory": "trajectory.csv" if os.path.isfile(os.path.join(run_dir, "trajectory.csv")) else None,
                  "render": (result or {}).get("render", {}).get("png"),
                  "scene_final": "scene_final.usda" if os.path.isfile(scene) else None,
                  "log": "logs/isaac_runtime.log"},
        notes=["acceptance uses maximum signed position over the full trajectory, not final pose alone",
               "livestream disabled; PNG is machine-checked for blankness but not visually confirmed by the agent"]))

    lines = [f"# S4 side-wall blocking {os.path.basename(run_dir)}", "",
             f"- UTC: {utc_now()}",
             f"- parcel-forge exit: {exit_code}; runtime exit: {launch['external_exit_code']}",
             f"- Physics coverage: {(result or {}).get('summary', {}).get('blocked_shots', 0)}/4 blocked",
             f"- Render: {(result or {}).get('render', {}).get('status', 'not_tested')}",
             f"- Effective CCD: {(result or {}).get('runtime_ccd_observation', {}).get('effective_status', 'unknown')}", "",
             "| shot | max signed centre (m) | centre limit (m) | overshoot (m) | verdict |",
             "| --- | ---: | ---: | ---: | --- |"]
    for shot in (result or {}).get("shots", []):
        lines.append(f"| {shot['label']} | {shot['max_signed_local_m']:.8f} | "
                     f"{shot['center_limit_m']:.8f} | {shot['overshoot_beyond_center_limit_m']:.8f} | "
                     f"{'pass' if shot['blocked'] and shot['reached_wall'] else 'fail'} |")
    contact = (result or {}).get("contact_settings", {})
    lines += ["", "## Contact settings", "",
              f"- Requested: {contact.get('requested', 'not_tested')}",
              f"- Readback layer: {contact.get('pre_play_composed_usd_readback', {}).get('readback_layer', 'not_tested')}",
              f"- Bound colliders: {len(contact.get('pre_play_composed_usd_readback', {}).get('colliders', []))}",
              f"- Tensor-level getter: {contact.get('pre_play_composed_usd_readback', {}).get('tensor_level_getter_available', 'unknown')}"]
    render = (result or {}).get("render", {})
    lines += ["", "## Evidence media", "",
              f"- Offline PNG: {render.get('png', 'not produced')}",
              f"- PNG status/statistics: {render.get('status', 'not_tested')} / {render.get('image_stats', 'n/a')}",
              "- WebRTC human confirmation: not_tested", "", "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for filename in sorted(files):
            lines.append(f"- {os.path.relpath(os.path.join(root, filename), run_dir)}")
    Path(os.path.join(run_dir, "summary.md")).write_text("\n".join(lines) + "\n")
    print(f"run: {run_dir}")
    print(f"coverage: {(result or {}).get('summary', {}).get('blocked_shots', 0)}/4 blocked")
    print(f"render: {render.get('status', 'not_tested')} {render.get('png', '')}")
    return exit_code
