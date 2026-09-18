"""Run directories, manifests and hashing.

Every claim in this project must point at a run directory. Run directories are
never reused and never overwritten: a new attempt gets a new id.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id(prefix: str) -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{prefix}"


def sha256_file(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, *args],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def code_version() -> dict:
    """Commit plus a hash of the dirty diff, so evidence binds to exact source."""
    commit = _git("rev-parse", "HEAD")
    diff = _git("diff", "HEAD")
    status = _git("status", "--porcelain")
    return {
        "commit": commit,
        "dirty": bool(status),
        "dirty_files": status.splitlines() if status else [],
        "dirty_diff_sha256": sha256_text(diff) if diff else None,
    }


def make_run_dir(prefix: str, base: str | None = None) -> str:
    base = base or os.path.join(REPO_ROOT, "runs")
    path = os.path.join(base, run_id(prefix))
    os.makedirs(os.path.join(path, "logs"), exist_ok=False)
    return path


def write_json(path: str, payload) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
    return path


def read_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def environment_snapshot(extra: dict | None = None) -> dict:
    """Host facts only. No environment variable dumps, no secrets."""
    snap = {
        "captured_utc": utc_now(),
        "host": platform.node(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "repo_root": REPO_ROOT,
        "code_version": code_version(),
    }
    if extra:
        snap.update(extra)
    return snap


def build_manifest(**fields) -> dict:
    """Manifest skeleton. Unknown values stay None; they are never guessed."""
    manifest = {
        "schema": "parcel_forge.manifest/1",
        "created_utc": utc_now(),
        "run_id": None,
        "stage": None,
        "case": None,
        "seed": None,
        "profile": None,
        "profile_sha256": None,
        "backend": None,
        "device": None,
        "dt": None,
        "command": None,
        "exit_code": None,
        "external_exit_code": None,
        "asset_path": None,
        "asset_sha256": None,
        "inputs_sha256": None,
        "code_version": code_version(),
        "evidence": {},
        "notes": [],
    }
    manifest.update(fields)
    return manifest


class Timer:
    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *exc):
        self.seconds = round(time.time() - self.t0, 3)
        return False


def make_unique_run_dir(label: str) -> str:
    """Allocate a fresh run without overwriting same-second evidence."""
    for attempt in range(100):
        try:
            return make_run_dir(label + (f"_{attempt}" if attempt else ""))
        except FileExistsError:
            continue
    raise RuntimeError("could not allocate fresh run directory")
