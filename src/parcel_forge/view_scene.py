"""Interactive WebRTC viewer for a parcel-forge run. Runs INSIDE the Isaac runtime.

Two things this does that a manual `simulate()` loop cannot:

1. **It plays the timeline.** `omni.physx.ui` registers its grab/push input actions
   only on a timeline PLAY event (`omni/physxui/scripts/input.py`: `use_actions(True)`
   under `TimelineEventType.PLAY`). A viewer that steps physics by calling
   `get_physx_simulation_interface().simulate()` directly never fires that event, so
   mouse dragging can never engage no matter how live the simulation is.

2. **It holds the probe until you are connected.** Physics that starts at load time
   is over before a human can see it: the probe's fall takes about 0.22 s, while a
   typical viewer runs several seconds of warm-up before it reports READY (D019).
   Here the probe is kinematic until the hold expires, so the drop happens while
   someone is watching.

This is a human-evidence tool. It never writes to `runs/` and its output is not
acceptance evidence: only a human can say what they saw on a stream.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv):
    p = argparse.ArgumentParser(description="Stream a parcel-forge scene over WebRTC")
    p.add_argument("--usd", required=True, help="absolute path to a scene .usda from a run")
    p.add_argument("--hold-seconds", type=float, default=20.0,
                   help="keep the probe frozen this long so you can connect before it drops")
    p.add_argument("--public-ip", default="140.113.203.85")
    p.add_argument("--signaling-port", type=int, default=49100)
    p.add_argument("--stream-port", type=int, default=47998)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--ui", action="store_true",
                   help="stream the full Isaac Sim editor (stage tree, property panel, "
                        "toolbar) instead of a bare viewport")
    p.add_argument("--paused", action="store_true", help="start with timeline stopped; do not hold or release the probe")
    p.add_argument("--probe-path", default="/World/Probe")
    p.add_argument("--dt", type=float, default=1 / 120.0)
    return p.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)

    # Livestream is NOT a SimulationApp config key -- `isaacsim/simulation_app.py`
    # has no such option, so passing {"livestream": 2} is silently ignored and
    # nothing ever binds a port. It is enabled by Kit command-line arguments, which
    # must be in sys.argv BEFORE SimulationApp is constructed. The port and
    # allowDynamicResize settings are mandatory: without them NVST fails to bind
    # (NVST_R_INTERNAL_ERROR).
    sys.argv += [
        f"--/exts/omni.kit.livestream.app/primaryStream/publicIp={args.public_ip}",
        f"--/exts/omni.kit.livestream.app/primaryStream/signalPort={args.signaling_port}",
        f"--/exts/omni.kit.livestream.app/primaryStream/streamPort={args.stream_port}",
        "--/exts/omni.kit.livestream.app/primaryStream/allowDynamicResize=false",
        "--/exts/omni.kit.livestream.app/primaryStream/streamType=webrtc",
        f"--/exts/omni.kit.livestream.app/primaryStream/targetFps={args.fps}",
        "--/app/window/width=1280",
        "--/app/window/height=720",
        "--/renderer/multiGpu/enabled=false",
        "--enable", "omni.kit.livestream.app",
        # Without this extension there is no mouse grab/push at all, whatever the
        # timeline is doing.
        "--enable", "omni.physx.ui",
    ]

    from isaacsim import SimulationApp

    # Which Kit "experience" is loaded decides whether there is any editor UI at all.
    # SimulationApp defaults to isaacsim.exp.base.python.kit, a minimal app that
    # renders a viewport and nothing else -- no stage tree, no property panel, no
    # toolbar. isaacsim.exp.full.streaming.kit is the shipped "Headless Isaac Sim
    # with Livestream using WebRTC" experience: it pulls in isaacsim.exp.full and
    # sets hideUi = false, so the whole editor is streamed.
    experience = ""
    if args.ui:
        import os as _os

        import isaacsim as _isaacsim

        experience = _os.path.join(_os.path.dirname(_isaacsim.__file__),
                                   "apps", "isaacsim.exp.full.streaming.kit")
        print(f"[VIEW] full editor experience: {experience}", flush=True)

    launch_config = {
        "headless": True,
        "enable_cameras": True,
        "width": 1280,
        "height": 720,
    }
    if args.ui:
        # Documented in simulation_app.py: "when headless is set to true, the UI is
        # hidden, set to false to override this behavior when live streaming".
        # Without this, choosing the full experience changes nothing a viewer can
        # see: headless still suppresses the UI and you get a bare viewport.
        launch_config["hide_ui"] = False

    app = SimulationApp(launch_config, experience=experience)

    import carb
    import omni.timeline
    import omni.usd
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    settings = carb.settings.get_settings()
    settings.set("/rtx/background/source/type", 2)
    settings.set("/rtx/background/source/color", (0.055, 0.065, 0.080))

    # The scene file is OPENED, not referenced: it is already a complete world
    # (ground, lights, box, probe, physics scene), so wrapping it in another stage
    # would only add a second floor to collide with.
    omni.usd.get_context().open_stage(args.usd)
    stage = omni.usd.get_context().get_stage()
    print(f"[VIEW] opened {args.usd}", flush=True)

    probe = stage.GetPrimAtPath(args.probe_path)
    if not probe or not probe.IsValid():
        print(f"[VIEW] WARNING: no probe at {args.probe_path}; nothing will be held", flush=True)
        probe = None

    held = False
    if not args.paused and probe is not None and probe.HasAPI(UsdPhysics.RigidBodyAPI):
        # Hold by switching gravity off, NOT by making the body kinematic. PhysX
        # rejects that combination outright:
        #   "kinematic bodies with CCD enabled are not supported! CCD will be ignored"
        # and CCD is exactly what stops the probe tunnelling through the 5 mm bottom
        # plate (D017). A gravity-disabled body stays dynamic, so CCD remains in
        # force, and it can still be pushed around while it waits.
        from pxr import PhysxSchema

        PhysxSchema.PhysxRigidBodyAPI.Apply(probe).CreateDisableGravityAttr(True)
        held = True

    timeline = omni.timeline.get_timeline_interface()
    timeline.set_target_framerate(1.0 / args.dt)
    timeline.set_looping(False)
    if args.paused:
        timeline.stop()
        print("[VIEW] timeline stopped: inspect saved pose before manually pressing Play", flush=True)
    else:
        timeline.play()   # enables mouse grab/push
        print("[VIEW] timeline playing: physics interaction (Shift + left-drag) is armed", flush=True)

    for _ in range(90):
        app.update()

    bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                             [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    try:
        from omni.kit.viewport.utility import get_active_viewport
        from omni.kit.viewport.utility.camera_state import ViewportCameraState

        viewport = get_active_viewport()

        # Frame on the objects under test, not on the scene furniture. A ground
        # slab several times wider than the box dominates a world-space bounding
        # box and parks the camera metres away from a 30 cm object -- which is
        # what "it starts very far away" was. Ground planes, lights and the
        # physics scene are infrastructure, not the subject.
        infra = ("groundplane", "floor", "light", "physicsscene", "render", "camera")
        subject_root = stage.GetPrimAtPath("/World")
        if not subject_root or not subject_root.IsValid():
            subject_root = stage.GetDefaultPrim()
        if not subject_root or not subject_root.IsValid():
            subject_root = stage.GetPseudoRoot()
        subjects = [child for child in subject_root.GetChildren()
                    if not any(marker in child.GetName().lower() for marker in infra)]
        if not subjects:
            subjects = [subject_root]

        lo = [float("inf")] * 3
        hi = [float("-inf")] * 3
        for subject in subjects:
            subject_range = bbox.ComputeWorldBound(subject).ComputeAlignedRange()
            if subject_range.IsEmpty():
                continue
            for i in range(3):
                lo[i] = min(lo[i], subject_range.GetMin()[i])
                hi[i] = max(hi[i], subject_range.GetMax()[i])

        centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
        radius = max(0.05, max(hi[i] - lo[i] for i in range(3)))
        print(f"[VIEW] framing on {[p.GetName() for p in subjects]}, "
              f"extent {radius:.3f} m", flush=True)
        state = ViewportCameraState(viewport.get_active_camera() or "/OmniverseKit_Persp", viewport)
        state.set_position_world(Gf.Vec3d(centre[0] + radius * 1.1,
                                          centre[1] - radius * 1.1,
                                          centre[2] + radius * 0.8), False)
        state.set_target_world(Gf.Vec3d(*centre), True)
        print(f"[VIEW] camera framed on {[round(c, 3) for c in centre]}", flush=True)
    except Exception as exc:  # pragma: no cover - viewport is optional
        print(f"[VIEW] camera framing skipped: {exc}", flush=True)

    print(f"[VIEW] READY - connect WebRTC to {args.public_ip}:{args.signaling_port}", flush=True)
    if held:
        print(f"[VIEW] the probe is HELD for {args.hold_seconds:.0f}s - connect now, "
              "then watch it drop", flush=True)

    import time

    released = not held
    start = time.time()
    while app.is_running():
        app.update()
        if not released and (time.time() - start) >= args.hold_seconds:
            from pxr import PhysxSchema

            PhysxSchema.PhysxRigidBodyAPI.Apply(probe).CreateDisableGravityAttr(False)
            released = True
            print("[VIEW] RELEASED - the probe is now dynamic; drag it with "
                  "Shift + left mouse drag", flush=True)

    app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
