"""Host orchestration for the bounded S4 PhysX mass-property readback."""

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
DEFAULT_PROFILE = os.path.join(REPO_ROOT, "profiles", "s4_mass_readback_v1.json")
IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "mass_readback_s4.py")


def _summary(run_dir, result, static_report, launch, exit_code):
    lines = [
        f"# S4 PhysX mass-property readback {os.path.basename(run_dir)}", "",
        f"- UTC: {utc_now()}",
        f"- Case: **{CASE_ID}**",
        f"- Runtime exit: {launch['external_exit_code']}",
        f"- parcel-forge exit: {exit_code}", "",
        "## Capability status", "",
        "| capability | status | evidence |", "| --- | --- | --- |",
        f"| dynamic USD authored and reopened | {(static_report or {}).get('summary', {}).get('verdict', 'unknown')} | validation.json |",
        f"| PhysX execution | {(result or {}).get('readback', {}).get('status', 'no_evidence')} | s4_mass_readback.json |",
        f"| PhysX mass/COM/inertia readback | {(result or {}).get('summary', {}).get('verdict', 'no_evidence')} | s4_mass_readback.json |",
        "| offline rendering | not_tested | outside this bounded step |",
        "| WebRTC human view | not_tested | no human confirmation in this run |", "",
        "## Numeric comparison", "",
        "| quantity | absolute error | tolerance | status |", "| --- | ---: | ---: | --- |",
    ]
    checks = {check["id"]: check for check in (result or {}).get("checks", [])}
    readback = (result or {}).get("readback", {})
    for key, label in (("mass_kg_absolute", "mass"),
                       ("com_m_absolute", "COM"),
                       ("inertia_kg_m2_absolute", "inertia tensor"),
                       ("principal_axes_quaternion_absolute", "principal axes")):
        check = checks.get(f"S4.physx_{key}", {})
        lines.append(f"| {label} | {readback.get('absolute_errors', {}).get(key, 'n/a')} | "
                     f"{readback.get('tolerances', {}).get(key, 'n/a')} | {check.get('status', 'not_tested')} |")
    lines += ["", "The comparison verifies that authored values reached PhysX. It does not "
              "validate the estimated shell mass or the uniform-cardboard assumption against a real box.", "",
              "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for filename in sorted(files):
            lines.append(f"- {os.path.relpath(os.path.join(root, filename), run_dir)}")
    return "\n".join(lines) + "\n"


def main(argv):
    profile, device, timeout = DEFAULT_PROFILE, None, 1800
    if "--profile" in argv:
        profile = argv[argv.index("--profile") + 1]
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])

    run_dir = make_run_dir("s4_mass_readback")
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    shutil.copy(profile, os.path.join(run_dir, "mass_readback_profile.json"))

    code, _, manifest = build_case(CASE_ID, run_dir=run_dir, device=device)
    static_report = None
    if code == EXIT_OK:
        code, static_report = validate_asset_in(run_dir, STATIC_PROFILE, device)
    if code != EXIT_OK or manifest is None:
        print(f"S4 mass readback stopped before simulation; evidence: {run_dir}")
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
         "--profile", os.path.join(run_dir, "mass_readback_profile.json")],
        log_path=os.path.join(run_dir, "logs", "physx_mass_readback.log"), timeout=timeout)

    result_path = os.path.join(run_dir, "s4_mass_readback.json")
    result = json.load(open(result_path, encoding="utf-8")) if os.path.isfile(result_path) else None
    if result is None:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    elif result.get("summary", {}).get("verdict") == "pass":
        exit_code = EXIT_OK
    elif result.get("readback", {}).get("status") == "error":
        exit_code = EXIT_ENV_FAIL
    else:
        exit_code = EXIT_ASSET_FAIL

    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir), stage="S4", case=CASE_ID,
        profile=os.path.basename(profile), profile_sha256=sha256_file(profile),
        backend="isaacsim-standalone 6.0.1.0 PhysX tensor view",
        device=launch["cuda_visible_devices"],
        dt=(result or {}).get("runtime", {}).get("physics_scene", {}).get("dt_readback"),
        command=launch["command_str"], exit_code=exit_code,
        external_exit_code=launch["external_exit_code"],
        asset_path="asset.usda", asset_sha256=sha256_file(os.path.join(run_dir, "asset.usda")),
        inputs_sha256={"case": sha256_file(os.path.join(run_dir, "request.json")),
                       "profile": sha256_file(profile),
                       "runtime_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={"environment": "environment.json", "request": "request.json",
                  "asset": "asset.usda", "build_manifest": "build_manifest.json",
                  "static_validation": "validation.json",
                  "result": "s4_mass_readback.json" if result else None,
                  "log": "logs/physx_mass_readback.log"},
        notes=["livestream disabled; the existing WebRTC viewer and its ports were not touched",
               "numeric readback agreement is distinct from real-box parameter accuracy"]))
    Path(os.path.join(run_dir, "summary.md")).write_text(
        _summary(run_dir, result, static_report, launch, exit_code))
    print(f"run: {run_dir}")
    for check in (result or {}).get("checks", []):
        print(f"  {check['status']:<8} {check['id']}: {check['detail']}")
    print(f"summary: {run_dir}/summary.md")
    return exit_code
