"""Host-side launcher: run a script inside the already-installed Isaac runtime.

This never installs, upgrades or reconfigures anything. It reproduces exactly
the environment the working WebRTC launcher uses, minus livestream, so the
user's live session and its ports are never touched.
"""

from __future__ import annotations

import os
import subprocess

from ..envprobe import load_isaac_env
from ..evidence import REPO_ROOT


def build_isaac_command(script: str, args: list[str], device_index: str | None = None) -> tuple[list[str], dict, str]:
    cfg = load_isaac_env()
    cmd = [cfg["isaac_python"], script, *args]

    env = dict(os.environ)
    env.update(cfg["env"])
    env["CUDA_VISIBLE_DEVICES"] = device_index or cfg["default_cuda_visible_devices"]
    preload = cfg.get("ld_preload")
    if preload:
        existing = env.get("LD_PRELOAD")
        env["LD_PRELOAD"] = f"{preload}:{existing}" if existing else preload
    # Let the in-runtime script import this package without installing it.
    src = os.path.join(REPO_ROOT, "src")
    env["PYTHONPATH"] = f"{src}:{env['PYTHONPATH']}" if env.get("PYTHONPATH") else src
    return cmd, env, cfg["isaac_cwd"]


class IsaacLauncher:
    """Runs an in-runtime script, streams its log to disk, returns the raw exit code."""

    def __init__(self, device_index: str | None = None):
        self.device_index = device_index

    def run(self, script: str, args: list[str], log_path: str, timeout: int = 1800) -> dict:
        cmd, env, cwd = build_isaac_command(script, args, self.device_index)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(f"# command: {' '.join(cmd)}\n")
            log.write(f"# cwd: {cwd}\n")
            log.write(f"# CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']}\n#\n")
            log.flush()
            try:
                proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=log,
                                      stderr=subprocess.STDOUT, timeout=timeout)
                rc, timed_out = proc.returncode, False
            except subprocess.TimeoutExpired:
                rc, timed_out = 124, True
                log.write(f"\n# TIMEOUT after {timeout}s\n")
        return {
            "command": cmd,
            "command_str": " ".join(cmd),
            "cwd": cwd,
            "cuda_visible_devices": env["CUDA_VISIBLE_DEVICES"],
            "external_exit_code": rc,
            "timed_out": timed_out,
            "log": log_path,
        }
