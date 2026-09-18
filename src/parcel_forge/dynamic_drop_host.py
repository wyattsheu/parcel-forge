"""Host orchestration for S4 dynamic-box drop and settling."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_INSUFFICIENT_EVIDENCE, EXIT_OK
from . import envprobe
from .build_host import DEFAULT_PROFILE as STATIC_PROFILE
from .build_host import build_case, validate_asset_in
from .evidence import (REPO_ROOT, build_manifest, environment_snapshot, make_run_dir,
                       sha256_file, utc_now, write_json)
from .runtime.launcher import IsaacLauncher

CASE_ID = "open_box_dynamic"
PROFILE = os.path.join(REPO_ROOT, "profiles", "s4_dynamic_drop_v1.json")
IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "dynamic_drop_s4.py")


def main(argv):
    device, timeout = None, 1800
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])

    run_dir = make_run_dir("s4_dynamic_drop")
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    shutil.copy(PROFILE, os.path.join(run_dir, "dynamic_drop_profile.json"))

    code, _, manifest = build_case(CASE_ID, run_dir=run_dir, device=device)
    static_report = None
    if code == EXIT_OK:
        code, static_report = validate_asset_in(run_dir, STATIC_PROFILE, device)
    if code != EXIT_OK or manifest is None:
        print(f"dynamic drop stopped before simulation: {run_dir}")
        return code

    gpu = envprobe.gpu_info()
    if gpu["status"] == "ok":
        free = max((item["memory_free_mib"] for item in gpu["gpus"]), default=0)
        if free < 8000:
            write_json(os.path.join(run_dir, "blocked.json"), {
                "blocked_utc": utc_now(),
                "reason": "insufficient free VRAM to start a new Isaac process",
                "max_free_vram_mib": free,
                "policy": "parcel-forge never stops foreign GPU processes or resets shared state",
            })
            print(f"BLOCKED: only {free} MiB free VRAM. Evidence: {run_dir}/blocked.json")
            return EXIT_ENV_FAIL

    launch = IsaacLauncher(device_index=device).run(
        IN_RUNTIME_SCRIPT,
        ["--out", run_dir, "--asset", os.path.join(run_dir, "asset.usda"),
         "--manifest", os.path.join(run_dir, "build_manifest.json"),
         "--profile", os.path.join(run_dir, "dynamic_drop_profile.json")],
        log_path=os.path.join(run_dir, "logs", "dynamic_drop.log"), timeout=timeout)

    result_path = os.path.join(run_dir, "s4_dynamic_drop.json")
    result = json.load(open(result_path, encoding="utf-8")) if os.path.isfile(result_path) else None
    log_path = os.path.join(run_dir, "logs", "dynamic_drop.log")
    log_text = Path(log_path).read_text(errors="replace") if os.path.isfile(log_path) else ""
    ccd_disabled = "CCD will be disabled" in log_text
    if result is not None:
        result["runtime_ccd_observation"] = {
            "scene_attribute_readback":
                result.get("runtime", {}).get("physics_scene", {}).get("ccd_enabled"),
            "disable_warning_observed": ccd_disabled,
            "effective_status": ("disabled_by_runtime_warning" if ccd_disabled
                                 else "not_confirmed_no_disable_warning_observed"),
            "evidence": "logs/dynamic_drop.log",
        }
        result.setdefault("checks", []).append({
            "id": "S4.dynamic_drop_ccd_effective_runtime_state",
            "status": "warning" if ccd_disabled else "unknown",
            "detail": ("scene attribute is true but runtime disabled CCD"
                       if ccd_disabled else "no disable warning; effective state not directly readable"),
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
        run_id=os.path.basename(run_dir), stage="S4", case=CASE_ID,
        profile=os.path.basename(PROFILE), profile_sha256=sha256_file(PROFILE),
        backend="isaacsim-standalone 6.0.1.0", device=launch["cuda_visible_devices"],
        dt=(result or {}).get("physics", {}).get("dt_s"), command=launch["command_str"],
        exit_code=exit_code, external_exit_code=launch["external_exit_code"],
        asset_path="scene_final.usda" if os.path.isfile(scene) else "asset.usda",
        asset_sha256=sha256_file(scene if os.path.isfile(scene)
                                 else os.path.join(run_dir, "asset.usda")),
        inputs_sha256={"case": sha256_file(os.path.join(run_dir, "request.json")),
                       "profile": sha256_file(PROFILE),
                       "runtime_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={"environment": "environment.json", "request": "request.json",
                  "profile": "dynamic_drop_profile.json", "asset": "asset.usda",
                  "static_validation": "validation.json",
                  "result": "s4_dynamic_drop.json" if result else None,
                  "trajectory": "trajectory.csv" if os.path.isfile(os.path.join(run_dir, "trajectory.csv")) else None,
                  "scene_final": "scene_final.usda" if os.path.isfile(scene) else None,
                  "log": "logs/dynamic_drop.log"},
        notes=["one rigid body on the root with five child colliders",
               "render not tested; scene_final.usda is available for WebRTC human inspection"]))

    physics = (result or {}).get("physics", {})
    lines = [f"# S4 dynamic-box drop {os.path.basename(run_dir)}", "",
             f"- UTC: {utc_now()}",
             f"- parcel-forge exit: {exit_code}; runtime exit: {launch['external_exit_code']}",
             f"- Static asset validation: {(static_report or {}).get('summary', {}).get('verdict', 'unknown')}",
             f"- Physics verdict: {(result or {}).get('summary', {}).get('verdict', 'no_evidence')}",
             f"- Effective CCD: {(result or {}).get('runtime_ccd_observation', {}).get('effective_status', 'unknown')}",
             f"- Final root z: {physics.get('final_state', {}).get('position_m', [None, None, None])[2]}",
             f"- Last-window max linear speed: {physics.get('settle_window_max_linear_speed_mps')}",
             f"- Last-window max angular speed: {physics.get('settle_window_max_angular_speed_radps')}", "",
             "## Checks", "", "| check | status | detail |", "| --- | --- | --- |"]
    for check in (result or {}).get("checks", []):
        lines.append(f"| {check['id']} | {check['status']} | {check['detail']} |")
    lines += ["", "## WebRTC self-check", "",
              f"Run: ./scripts/pf view --replace --run {os.path.basename(run_dir)} "
              "--scene scene_final.usda --ui",
              "Expected: one intact open box resting on the floor. Human confirmation remains not_tested.", "",
              "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for filename in sorted(files):
            lines.append(f"- {os.path.relpath(os.path.join(root, filename), run_dir)}")
    Path(os.path.join(run_dir, "summary.md")).write_text("\n".join(lines) + "\n")
    print(f"run: {run_dir}")
    print(f"physics verdict: {(result or {}).get('summary', {}).get('verdict', 'no_evidence')}")
    print(f"summary: {run_dir}/summary.md")
    return exit_code
