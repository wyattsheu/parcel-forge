"""Host side of `pf build`, `pf validate` and `pf verify` (S3).

Order matters: the schema runs first on the plain system Python. An illegal case
is rejected here, with a named error class, and no interpreter for the simulator
is ever started for it.
"""

from __future__ import annotations

import glob
import json
import os
import shutil

from . import EXIT_ASSET_FAIL, EXIT_ENV_FAIL, EXIT_OK
from . import envprobe
from .evidence import (REPO_ROOT, build_manifest, environment_snapshot, make_run_dir,
                       sha256_file, utc_now, write_json)
from .runtime.launcher import IsaacLauncher
from .schema import validate_file

USD_TOOL = os.path.join(REPO_ROOT, "src", "parcel_forge", "usd_tool.py")
CASES_DIR = os.path.join(REPO_ROOT, "cases")
INVALID_DIR = os.path.join(CASES_DIR, "invalid")
DEFAULT_PROFILE = os.path.join(REPO_ROOT, "profiles", "static_usd_v1.json")


def resolve_case(case_id: str) -> str | None:
    if os.path.isfile(case_id):
        return case_id
    for candidate in (os.path.join(CASES_DIR, f"{case_id}.json"),
                      os.path.join(CASES_DIR, "s4", f"{case_id}.json"),
                      os.path.join(INVALID_DIR, f"{case_id}.json")):
        if os.path.isfile(candidate):
            return candidate
    return None


def legal_case_ids() -> list[str]:
    return sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(CASES_DIR, "*.json")))


def invalid_case_ids() -> list[str]:
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(INVALID_DIR, "*.json"))
                  if not p.endswith("expected_errors.json"))


def _run_dir_for(prefix: str) -> str:
    run_dir = make_run_dir(prefix)
    write_json(os.path.join(run_dir, "environment.json"),
               environment_snapshot({"inventory": envprobe.inventory()}))
    return run_dir


def build_case(case_id: str, run_dir: str | None = None, device: str | None = None) -> tuple[int, str, dict | None]:
    """Schema first, then author the USD. Returns (exit_code, run_dir, build_manifest)."""
    path = resolve_case(case_id)
    if path is None:
        print(f"case not found: {case_id}")
        return EXIT_ENV_FAIL, "", None

    run_dir = run_dir or _run_dir_for(f"s3_build_{case_id}")
    shutil.copy(path, os.path.join(run_dir, "request.json"))

    findings = validate_file(path)
    write_json(os.path.join(run_dir, "schema_findings.json"), {
        "schema": "parcel_forge.schema_findings/1",
        "case": case_id, "checked_utc": utc_now(),
        "verdict": "rejected" if findings else "accepted",
        "error_classes": sorted({f["code"] for f in findings}),
        "findings": findings,
    })
    if findings:
        classes = sorted({f["code"] for f in findings})
        print(f"{case_id}: REJECTED by schema ({', '.join(classes)}); the simulator was never started")
        for f in findings:
            print(f"    [{f['code']}] {f['path']}: {f['message']}")
        write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
            run_id=os.path.basename(run_dir), stage="S3", case=case_id,
            command=f"scripts/pf build --case {case_id}", exit_code=EXIT_ASSET_FAIL,
            external_exit_code=None, backend="none (schema only, no USD, no Kit)",
            inputs_sha256={"case": sha256_file(path)},
            evidence={"request": "request.json", "schema_findings": "schema_findings.json"},
            notes=["rejected before authoring: no interpreter for the simulator was launched"]))
        return EXIT_ASSET_FAIL, run_dir, None

    launch = IsaacLauncher(device_index=device).run(
        USD_TOOL, ["build", "--case", os.path.join(run_dir, "request.json"), "--out", run_dir],
        log_path=os.path.join(run_dir, "logs", "build.log"), timeout=300)

    manifest_path = os.path.join(run_dir, "build_manifest.json")
    manifest = None
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    code = EXIT_OK if manifest else EXIT_ENV_FAIL
    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir), stage="S3", case=case_id,
        command=launch["command_str"], exit_code=code,
        external_exit_code=launch["external_exit_code"],
        backend="pxr (OpenUSD) inside the Isaac venv; Kit not started",
        asset_path="asset.usda" if manifest else None,
        asset_sha256=sha256_file(os.path.join(run_dir, "asset.usda")),
        inputs_sha256={"case": sha256_file(path), "author": sha256_file(
            os.path.join(REPO_ROOT, "src", "parcel_forge", "usd_author.py"))},
        evidence={"request": "request.json", "schema_findings": "schema_findings.json",
                  "asset": "asset.usda" if manifest else None,
                  "build_manifest": "build_manifest.json" if manifest else None,
                  "log": "logs/build.log"}))
    print(f"{case_id}: built -> {os.path.relpath(run_dir, REPO_ROOT)}/asset.usda" if manifest
          else f"{case_id}: build FAILED, see {run_dir}/logs/build.log")
    return code, run_dir, manifest


def validate_asset_in(run_dir: str, profile: str, device: str | None = None) -> tuple[int, dict | None]:
    shutil.copy(profile, os.path.join(run_dir, "static_profile.json"))
    launch = IsaacLauncher(device_index=device).run(
        USD_TOOL, ["validate",
                   "--asset", os.path.join(run_dir, "asset.usda"),
                   "--manifest", os.path.join(run_dir, "build_manifest.json"),
                   "--profile", os.path.join(run_dir, "static_profile.json"),
                   "--out", run_dir],
        log_path=os.path.join(run_dir, "logs", "validate.log"), timeout=300)
    report_path = os.path.join(run_dir, "validation.json")
    report = None
    if os.path.isfile(report_path):
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
    if report is None:
        return EXIT_ENV_FAIL, None
    return (EXIT_OK if report["summary"]["verdict"] == "pass" else EXIT_ASSET_FAIL), report


def _write_summary(run_dir, case_id, manifest, report, code):
    lines = [f"# S3 build+validate {os.path.basename(run_dir)}", "",
             f"- Case: **{case_id}**", f"- UTC: {utc_now()}",
             f"- parcel-forge exit code: {code}", ""]
    if manifest is None:
        findings = {}
        p = os.path.join(run_dir, "schema_findings.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                findings = json.load(fh)
        lines += ["## Schema", "",
                  f"Verdict: **{findings.get('verdict', 'unknown')}**",
                  f"Error classes: `{', '.join(findings.get('error_classes', []))}`", "",
                  "| code | path | message |", "| --- | --- | --- |"]
        for f in findings.get("findings", []):
            lines.append(f"| {f['code']} | `{f['path']}` | {f['message']} |")
        lines += ["", "No USD was authored and no simulator interpreter was started."]
    else:
        lines += ["## Built asset", "",
                  f"- File: `asset.usda`  (defaultPrim `{manifest['default_prim']}`)",
                  f"- Plates: {manifest['plate_count']}, body_mode `{manifest['body_mode']}`",
                  f"- Interior: {manifest['interior_length_m']:.4f} x {manifest['interior_width_m']:.4f} "
                  f"x {manifest['interior_height_m']:.4f} m, floor at local z = "
                  f"{manifest['interior_floor_local_z_m']:.4f} m",
                  f"- Plate volume: {manifest['plate_volume_m3']:.10f} m^3", ""]
        if report:
            lines += ["## Static validation (G1)", "",
                      f"Profile: `{report.get('profile')}`  tolerance {report['tolerance_m']} m", "",
                      "| rule | status | detail |", "| --- | --- | --- |"]
            for c in report["checks"]:
                lines.append(f"| {c['rule']} | {c['status']} | {c['detail']} |")
            lines += ["", f"**Verdict: {report['summary']['verdict']}** "
                      f"({report['summary']['failed']} failed, {report['summary']['blocked']} blocked)"]
    lines += ["", "## Files", ""]
    for root, _d, files in os.walk(run_dir):
        for f in sorted(files):
            lines.append(f"- `{os.path.relpath(os.path.join(root, f), run_dir)}`")
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def verify_case(case_id: str, profile: str, device: str | None = None) -> tuple[int, str, dict | None]:
    run_dir = _run_dir_for(f"s3_verify_{case_id}")
    code, run_dir, manifest = build_case(case_id, run_dir=run_dir, device=device)
    report = None
    if manifest is not None:
        code, report = validate_asset_in(run_dir, profile, device)
        with open(os.path.join(run_dir, "manifest.json"), encoding="utf-8") as fh:
            m = json.load(fh)
        m["exit_code"] = code
        m["profile"] = os.path.basename(profile)
        m["profile_sha256"] = sha256_file(profile)
        m["evidence"]["validation"] = "validation.json" if report else None
        m["evidence"]["validate_log"] = "logs/validate.log"
        write_json(os.path.join(run_dir, "manifest.json"), m)
    _write_summary(run_dir, case_id, manifest, report, code)
    return code, run_dir, report


def main(argv: list[str]) -> int:
    profile, device = DEFAULT_PROFILE, None
    if "--profile" in argv:
        profile = argv[argv.index("--profile") + 1]
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]

    if "--all" in argv:
        case_ids = legal_case_ids() + invalid_case_ids()
    elif "--case" in argv:
        case_ids = [argv[argv.index("--case") + 1]]
    else:
        print("usage: pf verify (--case <case-id> | --all) [--profile FILE]")
        print(f"legal cases:   {', '.join(legal_case_ids())}")
        print(f"invalid cases: {', '.join(invalid_case_ids())}")
        return EXIT_ENV_FAIL

    expected_errors = {}
    p = os.path.join(INVALID_DIR, "expected_errors.json")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            expected_errors = json.load(fh)["expected_error_class"]

    rows, worst = [], EXIT_OK
    for case_id in case_ids:
        code, run_dir, report = verify_case(case_id, profile, device)
        should_be_rejected = case_id in expected_errors
        if should_be_rejected:
            findings_path = os.path.join(run_dir, "schema_findings.json")
            got = []
            if os.path.isfile(findings_path):
                with open(findings_path, encoding="utf-8") as fh:
                    got = json.load(fh)["error_classes"]
            want = expected_errors[case_id]
            ok = want in got
            rows.append((case_id, "rejected: " + want, ("rejected: " + ", ".join(got)) if got else "ACCEPTED",
                         "pass" if ok else "fail", run_dir))
            if not ok:
                worst = EXIT_ASSET_FAIL
        else:
            observed = (report or {}).get("summary", {}).get("verdict", "no-evidence")
            rows.append((case_id, "built + G1 pass", observed, observed, run_dir))
            if code != EXIT_OK:
                worst = code

    if len(rows) > 1:
        table = ["# S3 case suite (schema -> USD -> static validation)", "",
                 f"Generated: {utc_now()}", "",
                 "| case | expected | observed | verdict | run |", "| --- | --- | --- | --- | --- |"]
        for case_id, expected, observed, verdict, run_dir in rows:
            table.append(f"| {case_id} | {expected} | {observed} | {verdict} | "
                         f"`{os.path.relpath(run_dir, REPO_ROOT)}` |")
        table += ["", "An invalid case that is ACCEPTED means the schema is blind, not that the "
                  "specification is fine.", ""]
        suite = os.path.join(REPO_ROOT, "runs", f"{os.path.basename(rows[-1][4])}_suite.md")
        with open(suite, "w", encoding="utf-8") as fh:
            fh.write("\n".join(table))
        print("\n".join(table[4:]))
        print(f"suite table: {suite}")
    return worst
