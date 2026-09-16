"""Host side of `pf view`: launch the interactive viewer against a run's scene.

Refuses to start if the WebRTC ports are already in use. parcel-forge never stops
another session to take a port -- that is the owner's decision, and the message
says which command to run.
"""

from __future__ import annotations

import glob
import os
import shutil

from . import EXIT_ENV_FAIL, EXIT_OK
from . import envprobe
from .evidence import REPO_ROOT
from .runtime.launcher import IsaacLauncher

VIEWER = os.path.join(REPO_ROOT, "src", "parcel_forge", "view_scene.py")


def resolve_scene(run: str, prefer: str) -> str | None:
    """Accept a run id, a run directory, or a direct .usda path."""
    if run.endswith(".usda") and os.path.isfile(run):
        return os.path.abspath(run)
    run_dir = run if os.path.isdir(run) else os.path.join(REPO_ROOT, "runs", run)
    if not os.path.isdir(run_dir):
        matches = sorted(glob.glob(os.path.join(REPO_ROOT, "runs", f"*{run}*")))
        if not matches:
            return None
        run_dir = matches[-1]
    for name in ([prefer] if prefer else []) + ["asset.usda", "scene_final.usda"]:
        candidate = os.path.join(run_dir, name)
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return None


def latest_run(pattern: str = "*_s2_*") -> str | None:
    runs = sorted(d for d in glob.glob(os.path.join(REPO_ROOT, "runs", pattern))
                  if os.path.isdir(d) and os.path.isfile(os.path.join(d, "asset.usda")))
    return runs[-1] if runs else None


def main(argv: list[str]) -> int:
    run = argv[argv.index("--run") + 1] if "--run" in argv else None
    scene_name = argv[argv.index("--scene") + 1] if "--scene" in argv else "asset.usda"
    hold = argv[argv.index("--hold-seconds") + 1] if "--hold-seconds" in argv else "20"
    device = argv[argv.index("--device") + 1] if "--device" in argv else None
    public_ip = argv[argv.index("--public-ip") + 1] if "--public-ip" in argv else None

    if run is None:
        run = latest_run()
        if run is None:
            print("no run with an asset.usda found; run `./scripts/pf box --all` first")
            return EXIT_ENV_FAIL
        print(f"no --run given, using the newest S2 run: {os.path.basename(run)}")

    scene = resolve_scene(run, scene_name)
    if scene is None:
        print(f"could not find a scene for: {run}")
        return EXIT_ENV_FAIL

    ports = envprobe.webrtc_ports()
    if ports.get("status") == "ok" and any(ports["ports_in_use"].values()):
        busy = [p for p, used in ports["ports_in_use"].items() if used]
        print(f"WebRTC port(s) {busy} are already in use by another session.")
        print("parcel-forge will not stop someone else's process. Free them first, e.g.:")
        print("  bash ~/handoff/robot129_pro6000_sim_20260913/tools/stop_usd_webrtc.sh")
        return EXIT_ENV_FAIL

    args = ["--usd", scene, "--hold-seconds", str(hold)]
    if public_ip:
        args += ["--public-ip", public_ip]

    print(f"scene:  {scene}")
    print(f"holding the probe for {hold}s after READY so you can connect first")
    log = os.path.join(REPO_ROOT, "runs", "viewer.log")
    launcher = IsaacLauncher(device_index=device)
    cmd, env, cwd = __import__("parcel_forge.runtime.launcher", fromlist=["build_isaac_command"]) \
        .build_isaac_command(VIEWER, args, device)
    print(f"command: {' '.join(cmd)}")
    print("streaming until you press Ctrl+C; log: " + log)
    result = launcher.run(VIEWER, args, log_path=log, timeout=86400)
    return EXIT_OK if result["external_exit_code"] == 0 else EXIT_ENV_FAIL
