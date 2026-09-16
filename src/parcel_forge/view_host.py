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


WEBRTC_PORTS = (49100, 47998)
VIEWER_MARKER = os.path.join("parcel_forge", "view_scene.py")


def port_owner() -> tuple[int, str] | None:
    """Return (pid, cmdline) of whatever holds a WebRTC port, or None.

    Knowing *who* holds the port is the whole point: an earlier version only
    reported that a port was busy and pointed at another project's stop script,
    which could not stop a parcel-forge process and left the user looping.
    """
    import re
    import subprocess

    try:
        out = subprocess.run(["ss", "-lntp"], capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return None
    for line in out.splitlines():
        if not any(f":{port} " in line for port in WEBRTC_PORTS):
            continue
        match = re.search(r"pid=(\d+)", line)
        if not match:
            return (-1, "unknown process (no pid reported by ss)")
        pid = int(match.group(1))
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                cmdline = fh.read().replace(b"\x00", b" ").decode(errors="replace").strip()
        except OSError:
            cmdline = "unknown"
        return (pid, cmdline)
    return None


def is_our_viewer(cmdline: str) -> bool:
    return VIEWER_MARKER in cmdline.replace("\\", "/")


def stop_our_viewer(pid: int) -> bool:
    """Stop a parcel-forge viewer. Kit ignores SIGTERM often enough that a
    SIGKILL fallback is required, otherwise the port stays held."""
    import signal
    import time

    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            return True
        except PermissionError:
            print(f"no permission to stop pid {pid}")
            return False
        for _ in range(20):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
    return False


def main(argv: list[str]) -> int:
    if "--stop" in argv:
        busy = port_owner()
        if busy is None:
            print("no WebRTC port is bound; nothing to stop")
            return EXIT_OK
        pid, cmdline = busy
        if not is_our_viewer(cmdline):
            print(f"pid {pid} is not a parcel-forge viewer; refusing to stop it:")
            print(f"  {cmdline[:150]}")
            return EXIT_ENV_FAIL
        ok = stop_our_viewer(pid)
        print(f"stopped parcel-forge viewer pid {pid}" if ok else f"could not stop pid {pid}")
        return EXIT_OK if ok else EXIT_ENV_FAIL

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

    busy = port_owner()
    if busy is not None:
        pid, cmdline = busy
        if is_our_viewer(cmdline):
            # Our own process. Telling the user to go find someone else's stop
            # script for it -- which is what the old message did -- sends them in a
            # circle, because that script cannot see a PID it never wrote.
            if "--force" in argv or "--replace" in argv:
                print(f"stopping the existing parcel-forge viewer (pid {pid})")
                stop_our_viewer(pid)
            else:
                print(f"A parcel-forge viewer is already streaming (pid {pid}).")
                print("It belongs to this project, so stop it with either of:")
                print("  ./scripts/pf view --stop")
                print(f"  ./scripts/pf view --replace --run {run if run else '<run-id>'}")
                return EXIT_ENV_FAIL
        else:
            print(f"WebRTC ports are held by another program (pid {pid}):")
            print(f"  {cmdline[:150]}")
            print("parcel-forge will not stop a process it did not start. If that is the")
            print("handoff viewer, its own stop command is:")
            print("  bash ~/handoff/robot129_pro6000_sim_20260913/tools/stop_usd_webrtc.sh")
            return EXIT_ENV_FAIL

    args = ["--usd", scene, "--hold-seconds", str(hold)]
    if public_ip:
        args += ["--public-ip", public_ip]
    if "--ui" in argv:
        args += ["--ui"]

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
