"""Host side of `pf smoke`: create the run dir, launch the Isaac runtime, seal evidence."""

from __future__ import annotations

import json
import os
import shutil

from . import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_INSUFFICIENT_EVIDENCE, EXIT_OK
from . import envprobe
from .evidence import (REPO_ROOT, build_manifest, environment_snapshot, make_run_dir,
                       sha256_file, utc_now, write_json)
from .runtime.launcher import IsaacLauncher

IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "smoke_s1.py")


def _summary_md(run_dir: str, result: dict | None, launch: dict, exit_code: int) -> str:
    lines = [
        f"# S1 smoke run {os.path.basename(run_dir)}",
        "",
        f"- UTC: {utc_now()}",
        f"- Command: `{launch['command_str']}`",
        f"- CWD: `{launch['cwd']}`  CUDA_VISIBLE_DEVICES={launch['cuda_visible_devices']}",
        f"- Raw runtime exit code: {launch['external_exit_code']}"
        + ("  (TIMED OUT)" if launch["timed_out"] else ""),
        f"- parcel-forge exit code: {exit_code}",
        "",
        "## Capability status (each reported separately)",
        "",
        "| capability | status | evidence |",
        "| --- | --- | --- |",
    ]
    if result:
        phys = result.get("physics", {})
        read = result.get("readback", {})
        rend = result.get("render", {})
        checks = {c["id"]: c for c in result.get("checks", [])}
        lines += [
            f"| physics execution | {phys.get('status')} | trajectory.csv, {phys.get('steps_executed')} steps, "
            f"sim_time_end={phys.get('sim_time_end_s')} s |",
            f"| state read-back | {read.get('status')} | trajectory.csv columns {','.join(read.get('fields', []))} |",
            "| headless (no GUI, no livestream) | pass | launched with SimulationApp(headless=True), "
            "livestream never enabled |",
            f"| offline PNG render | {rend.get('status')} | {rend.get('png', 'none')} |",
            f"| WebRTC human view | {checks.get('S1.webrtc_human_view', {}).get('status', 'not_tested')} | "
            "no agent evidence possible; a human must look |",
            "",
            "## Checks",
            "",
            "| id | status | detail |",
            "| --- | --- | --- |",
        ]
        for c in result.get("checks", []):
            lines.append(f"| {c['id']} | {c['status']} | {c['detail']} |")
        lines += ["", f"**Verdict: {result.get('summary', {}).get('verdict', 'unknown')}**"]
    else:
        lines += [
            "| physics execution | blocked | in-runtime script produced no result file |",
            "| state read-back | blocked | none |",
            "| headless | blocked | none |",
            "| offline PNG render | blocked | none |",
            "| WebRTC human view | not_tested | none |",
            "",
            "See `logs/isaac_runtime.log` for the failure.",
        ]
    lines += ["", "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), run_dir)
            lines.append(f"- `{rel}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    profile = os.path.join(REPO_ROOT, "profiles", "s1_smoke_v1.json")
    device = None
    timeout = 1800
    if "--profile" in argv:
        profile = argv[argv.index("--profile") + 1]
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])

    if not os.path.isfile(profile):
        print(f"profile not found: {profile}")
        return EXIT_ENV_FAIL

    # Refuse to start if the GPU cannot take another process; never kill anyone.
    gpu = envprobe.gpu_info()
    run_dir = make_run_dir("s1_smoke")
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    shutil.copy(profile, os.path.join(run_dir, "profile.json"))

    if gpu["status"] == "ok":
        free = max((g["memory_free_mib"] for g in gpu["gpus"]), default=0)
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
        ["--out", run_dir, "--profile", os.path.join(run_dir, "profile.json")],
        log_path=os.path.join(run_dir, "logs", "isaac_runtime.log"),
        timeout=timeout,
    )

    result_path = os.path.join(run_dir, "s1_result.json")
    result = None
    if os.path.isfile(result_path):
        with open(result_path, encoding="utf-8") as fh:
            result = json.load(fh)

    if result is None:
        exit_code = EXIT_INSUFFICIENT_EVIDENCE
    elif result.get("summary", {}).get("verdict") == "pass":
        exit_code = EXIT_OK
    elif result.get("physics", {}).get("status") in ("not_run", "error"):
        exit_code = EXIT_ENV_FAIL
    else:
        exit_code = EXIT_ASSET_FAIL

    png_rel = (result or {}).get("render", {}).get("png")
    manifest = build_manifest(
        run_id=os.path.basename(run_dir),
        stage="S1",
        case="s1_cube_drop",
        seed=None,
        profile=os.path.basename(profile),
        profile_sha256=sha256_file(profile),
        backend="isaacsim-standalone 6.0.1.0",
        device=launch["cuda_visible_devices"],
        dt=(result or {}).get("physics", {}).get("dt_s"),
        command=launch["command_str"],
        exit_code=exit_code,
        external_exit_code=launch["external_exit_code"],
        asset_path=None,
        asset_sha256=None,
        inputs_sha256={"profile": sha256_file(profile),
                       "smoke_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={
            "environment": "environment.json",
            "profile": "profile.json",
            "log": "logs/isaac_runtime.log",
            "result": "s1_result.json" if result else None,
            "trajectory": "trajectory.csv" if os.path.isfile(os.path.join(run_dir, "trajectory.csv")) else None,
            "render": png_rel,
        },
        notes=[
            "S1 authors the scene procedurally in-memory; no .usda asset is written yet (that starts at S2/S3).",
            "livestream disabled; the pre-existing WebRTC session and its ports were not touched",
        ],
    )
    write_json(os.path.join(run_dir, "manifest.json"), manifest)
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(_summary_md(run_dir, result, launch, exit_code))

    print(f"run: {run_dir}")
    print(f"raw runtime exit={launch['external_exit_code']}  pf exit={exit_code}")
    if result:
        for c in result["checks"]:
            print(f"  {c['status']:<10} {c['id']}: {c['detail']}")
    print(f"summary: {run_dir}/summary.md")
    return exit_code
