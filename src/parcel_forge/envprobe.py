"""Read-only environment inventory.

Rules: never print environment variable dumps or secrets, never start or stop
anyone else's process, never install or upgrade anything. Anything we did not
actually measure is reported as "unknown" or "not_tested", never "pass".
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys

from .evidence import REPO_ROOT, utc_now

CONFIG_PATH = os.path.join(REPO_ROOT, "config", "isaac_env.json")


def load_isaac_env() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "executable not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # pragma: no cover - defensive
        return 1, "", repr(exc)


def host_info() -> dict:
    return {
        "user": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "hostname": platform.node(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "system_python": sys.version.split()[0],
        "cwd": os.getcwd(),
    }


def gpu_info() -> dict:
    """GPU inventory plus which GPU processes already exist. We never kill them."""
    if shutil.which("nvidia-smi") is None:
        return {"status": "unknown", "reason": "nvidia-smi not on PATH"}
    rc, out, err = _run([
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ])
    if rc != 0:
        return {"status": "unknown", "reason": err or f"exit {rc}"}
    gpus = []
    for line in out.splitlines():
        idx, name, total, used, util = [f.strip() for f in line.split(",")]
        gpus.append({
            "index": int(idx),
            "name": name,
            "memory_total_mib": int(total),
            "memory_used_mib": int(used),
            "utilization_pct": int(util),
            "memory_free_mib": int(total) - int(used),
        })
    rc2, out2, _ = _run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"])
    others = []
    if rc2 == 0 and out2:
        for line in out2.splitlines():
            pid, mem = [f.strip() for f in line.split(",")]
            others.append({"pid": int(pid), "used_mib": int(mem)})
    rc3, drv, _ = _run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
    return {
        "status": "ok",
        "driver_version": drv.splitlines()[0] if rc3 == 0 and drv else "unknown",
        "gpus": gpus,
        "pre_existing_compute_processes": others,
    }


def git_info() -> dict:
    rc, out, _ = _run(["git", "-C", REPO_ROOT, "rev-parse", "--abbrev-ref", "HEAD"])
    branch = out if rc == 0 else "unknown"
    rc2, out2, _ = _run(["git", "-C", REPO_ROOT, "status", "--porcelain"])
    rc3, out3, _ = _run(["git", "-C", REPO_ROOT, "rev-parse", "HEAD"])
    return {
        "repo_root": REPO_ROOT,
        "is_git_repo": rc == 0,
        "branch": branch,
        "commit": out3 if rc3 == 0 else None,
        "working_tree_clean": rc2 == 0 and not out2,
        "changed_entries": len(out2.splitlines()) if rc2 == 0 and out2 else 0,
    }


def isaac_packages() -> dict:
    """Version read-back from the Isaac venv. Imports metadata only; Kit is not booted."""
    cfg = load_isaac_env()
    python = cfg["isaac_python"]
    if not os.path.isfile(python):
        return {"status": "missing", "isaac_python": python, "reason": "interpreter not found"}
    snippet = (
        "import importlib.metadata as m, json, sys, pathlib\n"
        "names=['isaacsim','isaacsim-kernel','isaacsim-core','isaacsim-app','isaaclab','torch','numpy',"
        "'usd-core','pydantic','warp-lang']\n"
        "out={}\n"
        "for n in names:\n"
        "    try: out[n]=m.version(n)\n"
        "    except Exception: out[n]=None\n"
        "vf=pathlib.Path(m.distribution('isaacsim').locate_file('isaacsim'))/'VERSION'\n"
        "out['_version_file']=vf.read_text().strip() if vf.is_file() else None\n"
        "out['_python']=sys.version.split()[0]\n"
        "print(json.dumps(out))\n"
    )
    rc, out, err = _run([python, "-c", snippet], timeout=90)
    if rc != 0:
        return {"status": "error", "isaac_python": python, "reason": err[-400:] or f"exit {rc}"}
    data = json.loads(out.splitlines()[-1])
    return {
        "status": "ok",
        "isaac_python": python,
        "python": data.pop("_python"),
        "isaacsim_version_file": data.pop("_version_file"),
        "packages": data,
    }


def webrtc_ports(cfg: dict | None = None) -> dict:
    """Check whether the user's existing WebRTC session is listening. Do not disturb it."""
    cfg = cfg or load_isaac_env()
    ports = [cfg["do_not_touch"]["webrtc_signaling_port"], cfg["do_not_touch"]["webrtc_stream_port"]]
    if shutil.which("ss") is None:
        return {"status": "unknown", "reason": "ss not available", "ports": ports}
    rc, out, _ = _run(["ss", "-lntu"])
    if rc != 0:
        return {"status": "unknown", "reason": "ss failed", "ports": ports}
    in_use = {p: any(f":{p} " in line for line in out.splitlines()) for p in ports}
    return {
        "status": "ok",
        "ports_in_use": in_use,
        "interpretation": (
            "at least one WebRTC port is bound: an existing viewer session is assumed live and untouched"
            if any(in_use.values())
            else "no WebRTC port bound right now; existing session may have been stopped by its owner"
        ),
    }


def inventory() -> dict:
    cfg = load_isaac_env()
    return {
        "schema": "parcel_forge.env_inventory/1",
        "captured_utc": utc_now(),
        "host": host_info(),
        "git": git_info(),
        "gpu": gpu_info(),
        "isaac": isaac_packages(),
        "isaac_env_config": cfg,
        "webrtc": webrtc_ports(cfg),
    }
