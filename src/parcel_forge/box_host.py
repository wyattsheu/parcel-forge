"""Host side of `pf box`: validate the spec first, then run one case per run directory."""

from __future__ import annotations

import glob
import json
import os
import shutil

from . import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_INSUFFICIENT_EVIDENCE, EXIT_OK
from . import envprobe
from .evidence import (REPO_ROOT, build_manifest, environment_snapshot, make_run_dir,
                       sha256_file, utc_now, write_json)
from .geometry import validate_box_spec
from .runtime.launcher import IsaacLauncher

IN_RUNTIME_SCRIPT = os.path.join(REPO_ROOT, "src", "parcel_forge", "box_s2.py")
CASES_DIR = os.path.join(REPO_ROOT, "cases")
DEFAULT_PROFILE = os.path.join(REPO_ROOT, "profiles", "open_box_v1.json")


def case_path(case_id: str) -> str:
    return case_id if os.path.isfile(case_id) else os.path.join(CASES_DIR, f"{case_id}.json")


def all_case_ids() -> list[str]:
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(CASES_DIR, "*.json")))


def _summary_md(run_dir, case, result, launch, exit_code) -> str:
    lines = [
        f"# S2 open-box run {os.path.basename(run_dir)}",
        "",
        f"- Case: **{case['case_id']}**  (fault: `{case['geometry']['fault']}`)",
        f"- Expected outcome: **{case['expected_outcome']}**",
        f"- Observed outcome: **{(result or {}).get('outcome', {}).get('outcome', 'none')}**",
        f"- UTC: {utc_now()}",
        f"- Command: `{launch['command_str']}`",
        f"- CWD: `{launch['cwd']}`  CUDA_VISIBLE_DEVICES={launch['cuda_visible_devices']}",
        f"- Raw runtime exit code: {launch['external_exit_code']}"
        + ("  (TIMED OUT)" if launch["timed_out"] else ""),
        f"- parcel-forge exit code: {exit_code}",
        "",
    ]
    if result:
        phys = result.get("physics", {})
        outcome = result.get("outcome", {})
        rend = result.get("render", {})
        lines += [
            "## Capability status (reported separately)",
            "",
            "| capability | status | evidence |",
            "| --- | --- | --- |",
            f"| static geometry read-back | {'pass' if all(c['status'] == 'pass' for c in result['checks'] if c['id'].startswith('S2.plate')) else 'fail'} | geometry_readback in s2_result.json |",
            f"| USD asset written | {'pass' if result.get('asset') else 'fail'} | asset.usda |",
            f"| physics execution | {phys.get('status')} | trajectory.csv, {phys.get('steps_executed')} steps |",
            f"| local-frame outcome judgement | {outcome.get('outcome')} | {outcome.get('judged_in')} |",
            f"| offline PNG render | {rend.get("status")} | {", ".join(v.get("png", "none") for v in rend.get("views", []))} |",
            "| WebRTC human view | not_tested | no agent evidence possible |",
            "",
            "## Measured positions",
            "",
            f"- Final world position: {phys.get('final_world_position_m')}",
            f"- Final box-local position: {phys.get('final_box_local_position_m')}",
            f"- Lowest box-local z reached: {phys.get('min_box_local_z_m')}",
            f"- Final speed: {phys.get('final_speed_mps')} m/s",
            "",
            f"Reason: {outcome.get('reason')}",
            "",
            "## Checks",
            "",
            "| id | status | detail |",
            "| --- | --- | --- |",
        ]
        for c in result["checks"]:
            lines.append(f"| {c['id']} | {c['status']} | {c['detail']} |")
        lines += ["", f"**Verdict: {result.get('summary', {}).get('verdict', 'unknown')}**"]
    else:
        lines += ["No result file was produced; see `logs/isaac_runtime.log`.",
                  "This run is recorded as insufficient evidence, not as a pass or a failure of the asset."]
    lines += ["", "## Files", ""]
    for root, _dirs, files in os.walk(run_dir):
        for f in sorted(files):
            lines.append(f"- `{os.path.relpath(os.path.join(root, f), run_dir)}`")
    return "\n".join(lines) + "\n"


def run_case(case_id: str, profile: str, device: str | None, timeout: int) -> tuple[int, str, dict | None]:
    path = case_path(case_id)
    if not os.path.isfile(path):
        print(f"case not found: {case_id} (looked in {CASES_DIR})")
        return EXIT_ENV_FAIL, "", None
    with open(path, encoding="utf-8") as fh:
        case = json.load(fh)

    run_dir = make_run_dir(f"s2_{case['case_id']}")
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    shutil.copy(path, os.path.join(run_dir, "request.json"))
    shutil.copy(profile, os.path.join(run_dir, "profile.json"))

    # Reject an unbuildable specification before spending a simulator launch on it.
    g = case["geometry"]
    errors = validate_box_spec(g["outer_size_m"], g["wall_thickness_m"], g.get("fault", "none"))
    if errors:
        write_json(os.path.join(run_dir, "s2_result.json"), {
            "case_id": case["case_id"], "checks": [
                {"id": "S2.spec_valid", "status": "fail", "detail": "; ".join(errors)}],
            "summary": {"verdict": "fail", "observed_outcome": "spec_rejected"},
        })
        print(f"{case['case_id']}: spec rejected before launch: {'; '.join(errors)}")
        return EXIT_ASSET_FAIL, run_dir, None

    gpu = envprobe.gpu_info()
    if gpu["status"] == "ok":
        free = max((g_["memory_free_mib"] for g_ in gpu["gpus"]), default=0)
        if free < 8000:
            write_json(os.path.join(run_dir, "blocked.json"), {
                "blocked_utc": utc_now(), "reason": "insufficient free VRAM to start a new Isaac process",
                "max_free_vram_mib": free,
                "policy": "parcel-forge never stops foreign GPU processes or resets shared state",
            })
            print(f"BLOCKED: only {free} MiB free VRAM. Evidence: {run_dir}/blocked.json")
            return EXIT_ENV_FAIL, run_dir, None

    launch = IsaacLauncher(device_index=device).run(
        IN_RUNTIME_SCRIPT,
        ["--out", run_dir, "--case", os.path.join(run_dir, "request.json"),
         "--profile", os.path.join(run_dir, "profile.json")],
        log_path=os.path.join(run_dir, "logs", "isaac_runtime.log"),
        timeout=timeout,
    )

    result_path = os.path.join(run_dir, "s2_result.json")
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

    asset = os.path.join(run_dir, "asset.usda")
    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir), stage="S2", case=case["case_id"], seed=case.get("seed"),
        profile=os.path.basename(profile), profile_sha256=sha256_file(profile),
        backend="isaacsim-standalone 6.0.1.0", device=launch["cuda_visible_devices"],
        dt=(result or {}).get("physics", {}).get("dt_s"),
        command=launch["command_str"], exit_code=exit_code,
        external_exit_code=launch["external_exit_code"],
        asset_path="asset.usda" if os.path.isfile(asset) else None,
        asset_sha256=sha256_file(asset),
        inputs_sha256={"case": sha256_file(path), "profile": sha256_file(profile),
                       "box_script": sha256_file(IN_RUNTIME_SCRIPT)},
        evidence={"environment": "environment.json", "request": "request.json",
                  "profile": "profile.json", "asset": "asset.usda" if os.path.isfile(asset) else None,
                  "result": "s2_result.json" if result else None,
                  "trajectory": "trajectory.csv" if os.path.isfile(os.path.join(run_dir, "trajectory.csv")) else None,
                  "render": (result or {}).get("render", {}).get("png"),
                  "log": "logs/isaac_runtime.log"},
        notes=[f"expected outcome: {case['expected_outcome']}",
               "outcome judged in the box local frame so world-floor support cannot pass as a box floor",
               "livestream disabled; the pre-existing WebRTC session was not touched"],
    ))
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write(_summary_md(run_dir, case, result, launch, exit_code))
    return exit_code, run_dir, result


def main(argv: list[str]) -> int:
    profile, device, timeout = DEFAULT_PROFILE, None, 1800
    if "--profile" in argv:
        profile = argv[argv.index("--profile") + 1]
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])

    if "--all" in argv:
        case_ids = all_case_ids()
    elif "--case" in argv:
        case_ids = [argv[argv.index("--case") + 1]]
    else:
        print("usage: pf box (--case <case-id> | --all) [--profile FILE] [--device N] [--timeout SEC]")
        print(f"available cases: {', '.join(all_case_ids())}")
        return EXIT_ENV_FAIL

    if not os.path.isfile(profile):
        print(f"profile not found: {profile}")
        return EXIT_ENV_FAIL

    rows, worst = [], EXIT_OK
    for case_id in case_ids:
        code, run_dir, result = run_case(case_id, profile, device, timeout)
        observed = (result or {}).get("summary", {}).get("observed_outcome", "none")
        expected = (result or {}).get("expected_outcome", "?")
        verdict = (result or {}).get("summary", {}).get("verdict", "no-evidence")
        rows.append((case_id, expected, observed, verdict, code, run_dir))
        print(f"{case_id}: expected={expected} observed={observed} verdict={verdict} exit={code}")
        if code != EXIT_OK:
            worst = code

    if len(rows) > 1:
        table = ["# S2 case suite", "", f"Generated: {utc_now()}", "",
                 "| case | expected | observed | verdict | pf exit | run |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for case_id, expected, observed, verdict, code, run_dir in rows:
            table.append(f"| {case_id} | {expected} | {observed} | {verdict} | {code} | "
                         f"`{os.path.relpath(run_dir, REPO_ROOT)}` |")
        table += ["", "A fault case whose observed outcome is `inside` means the check is blind, "
                  "not that the asset is good.", ""]
        suite_path = os.path.join(REPO_ROOT, "runs", f"{os.path.basename(rows[-1][5])}_suite.md")
        with open(suite_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(table))
        print("\n".join(table[4:]))
        print(f"suite table: {suite_path}")
    return worst
