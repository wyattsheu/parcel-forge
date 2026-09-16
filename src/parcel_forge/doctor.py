"""`pf doctor` - environment health report.

Every check reports one of: pass, fail, warn, not_tested, unknown.
Checks this tool does not actually perform are reported as `not_tested`.
Booting Kit, stepping physics and rendering are NOT doctor's job: they are
proven by `pf smoke` and its saved run evidence.
"""

from __future__ import annotations

import os

from . import EXIT_ENV_FAIL, EXIT_OK, __version__
from . import envprobe
from .evidence import build_manifest, make_run_dir, utc_now, write_json

MIN_FREE_VRAM_MIB = 8000


def _check(name, status, detail, evidence=None):
    return {"check": name, "status": status, "detail": detail, "evidence": evidence}


def run_checks(inv: dict) -> list[dict]:
    checks = []

    host = inv["host"]
    checks.append(_check("host_readable", "pass", f"{host['user']}@{host['hostname']} on {host['os']}"))

    git = inv["git"]
    checks.append(_check(
        "repo_is_git",
        "pass" if git["is_git_repo"] else "fail",
        f"branch={git['branch']} commit={git['commit']} clean={git['working_tree_clean']} changed={git['changed_entries']}",
    ))

    cfg = inv["isaac_env_config"]
    python_ok = os.path.isfile(cfg["isaac_python"])
    checks.append(_check(
        "isaac_python_present",
        "pass" if python_ok else "fail",
        cfg["isaac_python"],
    ))

    isaac = inv["isaac"]
    if isaac["status"] == "ok":
        pkgs = isaac["packages"]
        checks.append(_check(
            "isaac_version_readback",
            "pass",
            f"isaacsim={pkgs.get('isaacsim')} VERSION={isaac['isaacsim_version_file']} python={isaac['python']}",
        ))
        checks.append(_check(
            "usd_via_pxr",
            "not_tested",
            "pxr ships inside the Isaac runtime, not as a usd-core wheel; import is exercised by `pf smoke`, not here",
        ))
    else:
        checks.append(_check("isaac_version_readback", "fail", isaac.get("reason", "unknown")))

    gpu = inv["gpu"]
    if gpu["status"] == "ok":
        free = [g["memory_free_mib"] for g in gpu["gpus"]]
        best = max(free) if free else 0
        checks.append(_check(
            "gpu_available",
            "pass" if best >= MIN_FREE_VRAM_MIB else "fail",
            f"driver={gpu['driver_version']} gpus={len(gpu['gpus'])} max_free_vram_mib={best} "
            f"(need >= {MIN_FREE_VRAM_MIB})",
        ))
        checks.append(_check(
            "pre_existing_gpu_processes",
            "warn" if gpu["pre_existing_compute_processes"] else "pass",
            f"{len(gpu['pre_existing_compute_processes'])} foreign compute process(es) present; "
            "parcel-forge never stops them",
            gpu["pre_existing_compute_processes"],
        ))
    else:
        checks.append(_check("gpu_available", "unknown", gpu.get("reason", "unknown")))

    web = inv["webrtc"]
    if web["status"] == "ok":
        checks.append(_check(
            "webrtc_session_untouched",
            "pass",
            web["interpretation"] + "; parcel-forge runs headless with livestream disabled",
            web["ports_in_use"],
        ))
    else:
        checks.append(_check("webrtc_session_untouched", "unknown", web.get("reason", "unknown")))

    for name, why in [
        ("kit_boot", "booting Kit takes ~30 s; proven by `pf smoke`, see its run manifest"),
        ("physics_step_readback", "proven by `pf smoke` trajectory.csv"),
        ("offline_render_png", "proven by `pf smoke` renders/ and image stats"),
        ("webrtc_human_view", "requires a human to look at the stream; an agent cannot self-certify this"),
    ]:
        checks.append(_check(name, "not_tested", why))

    return checks


def overall(checks: list[dict]) -> str:
    if any(c["status"] == "fail" for c in checks):
        return "fail"
    if any(c["status"] == "warn" for c in checks):
        return "warn"
    return "pass"


def main(argv: list[str]) -> int:
    out_dir = None
    if "--out" in argv:
        out_dir = argv[argv.index("--out") + 1]

    inv = envprobe.inventory()
    checks = run_checks(inv)
    status = overall(checks)

    report = {
        "schema": "parcel_forge.doctor/1",
        "tool_version": __version__,
        "generated_utc": utc_now(),
        "overall": status,
        "legend": {
            "pass": "actually measured and healthy",
            "warn": "measured, usable, but note the detail",
            "fail": "measured and broken",
            "not_tested": "this tool did not test it; do not report it as passing",
            "unknown": "could not be determined read-only",
        },
        "checks": checks,
        "inventory": inv,
    }

    run_dir = out_dir or make_run_dir("doctor")
    os.makedirs(run_dir, exist_ok=True)
    doctor_path = write_json(os.path.join(run_dir, "doctor.json"), report)
    write_json(os.path.join(run_dir, "environment.json"), inv)
    write_json(os.path.join(run_dir, "manifest.json"), build_manifest(
        run_id=os.path.basename(run_dir),
        stage="S0",
        command="scripts/pf doctor",
        exit_code=EXIT_OK if status != "fail" else EXIT_ENV_FAIL,
        backend="none (read-only inventory)",
        evidence={"doctor": "doctor.json", "environment": "environment.json"},
        notes=["doctor does not boot Kit; not_tested entries are proven by `pf smoke`"],
    ))

    width = max(len(c["check"]) for c in checks)
    print(f"parcel-forge doctor  overall={status}")
    for c in checks:
        print(f"  {c['status']:<11} {c['check']:<{width}}  {c['detail']}")
    print(f"report: {doctor_path}")
    return EXIT_OK if status != "fail" else EXIT_ENV_FAIL
