"""Isaac Sim 6.0.x standalone adapter. Runs INSIDE the Isaac Python runtime.

API notes for this exact install (isaacsim 6.0.1.0, VERSION 6.0.1-rc.7):
  * `isaacsim.core.api` (the 4.x World/DynamicCuboid API) does not exist here.
    6.0 exposes `isaacsim.core.simulation_manager.SimulationManager` plus
    `isaacsim.core.experimental.prims`. This adapter targets those.
  * `SimulationApp` must be constructed before any Kit-dependent import.
  * We use the Isaac Sim standalone launcher only. Isaac Lab's AppLauncher is
    installed in the same venv but is deliberately NOT used: mixing two
    launchers is out of scope and the project must not depend on Isaac Lab.

The adapter owns launch / configure / step / read-back / render / close, so
schema, geometry and validation layers never import Kit directly.
"""

from __future__ import annotations

import math


class IsaacSimRuntime:
    backend_name = "isaacsim-standalone"

    def __init__(self, dt: float = 1.0 / 240.0, device: str = "cuda:0",
                 headless: bool = True, enable_cameras: bool = True):
        self.dt = dt
        self.device = device
        self.headless = headless
        self.enable_cameras = enable_cameras
        self.app = None
        self.stage = None
        self._sim = None
        self._timeline = None
        self._started = False

    # ---- lifecycle ------------------------------------------------------
    def start(self) -> dict:
        from isaacsim import SimulationApp

        # livestream is intentionally absent: the user's WebRTC session owns
        # the livestream ports and must not be disturbed.
        self.app = SimulationApp({"headless": self.headless, "enable_cameras": self.enable_cameras})

        import omni.timeline
        import omni.usd
        from isaacsim.core.simulation_manager import SimulationManager
        from pxr import UsdGeom

        self._sim = SimulationManager
        self._timeline = omni.timeline.get_timeline_interface()
        self.stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1.0)
        self._started = True
        return self.runtime_info()

    def runtime_info(self) -> dict:
        import platform
        import sys

        info = {
            "backend": self.backend_name,
            "adapter": "parcel_forge.runtime.isaacsim_runtime",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "headless": self.headless,
            "enable_cameras": self.enable_cameras,
            "livestream": False,
            "requested_dt": self.dt,
            "requested_device": self.device,
        }
        try:
            from isaacsim.core.version import get_version

            v = get_version()
            info["isaacsim_version"] = v[0] if isinstance(v, (list, tuple)) else str(v)
        except Exception as exc:
            info["isaacsim_version"] = f"unknown ({exc.__class__.__name__})"
        return info

    def configure_physics(self, gravity: float = -9.81) -> dict:
        """Create/patch the PhysX scene and report the values actually read back."""
        from pxr import Gf, PhysxSchema, UsdPhysics

        self._sim.setup_simulation(dt=self.dt, device=self.device)

        scene_prim = None
        for prim in self.stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                scene_prim = prim
                break
        if scene_prim is None:
            scene = UsdPhysics.Scene.Define(self.stage, "/PhysicsScene")
            scene_prim = scene.GetPrim()
        scene = UsdPhysics.Scene(scene_prim)
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(abs(gravity))

        physx = PhysxSchema.PhysxSceneAPI.Apply(scene_prim)
        read_back = {
            "physics_scene_path": str(scene_prim.GetPath()),
            "gravity_direction": list(scene.GetGravityDirectionAttr().Get()),
            "gravity_magnitude": float(scene.GetGravityMagnitudeAttr().Get()),
            "dt_readback": float(self._sim.get_physics_dt()),
            "device_readback": str(self._sim.get_device()),
            "solver_type": physx.GetSolverTypeAttr().Get(),
            "gpu_dynamics": physx.GetEnableGPUDynamicsAttr().Get(),
            "time_steps_per_second": physx.GetTimeStepsPerSecondAttr().Get(),
        }
        return {k: (str(v) if v is not None and not isinstance(v, (int, float, list, str, bool)) else v)
                for k, v in read_back.items()}

    def play(self) -> None:
        self._timeline.play()
        self.app.update()

    def step(self, steps: int = 1, render: bool = False) -> None:
        self._sim.step(steps=steps)
        if render:
            self.app.update()

    @property
    def sim_time(self) -> float:
        return float(self._sim.get_simulation_time())

    def close(self) -> None:
        if self.app is not None:
            try:
                self._timeline.stop()
            except Exception:
                pass
            self.app.close()
            self.app = None
            self._started = False

    # ---- authoring ------------------------------------------------------
    def add_ground_plane(self, path: str = "/World/GroundPlane", size: float = 20.0,
                         z: float = 0.0) -> str:
        from pxr import Gf, UsdGeom, UsdPhysics

        UsdGeom.Xform.Define(self.stage, "/World")
        plane = UsdGeom.Plane.Define(self.stage, path)
        plane.CreateAxisAttr("Z")
        plane.CreateWidthAttr(size)
        plane.CreateLengthAttr(size)
        plane.CreatePurposeAttr(UsdGeom.Tokens.guide)  # collider only; drawn separately below
        UsdGeom.XformCommonAPI(plane).SetTranslate(Gf.Vec3d(0.0, 0.0, z))
        UsdPhysics.CollisionAPI.Apply(plane.GetPrim())

        # A visible slab so the render shows a floor (UsdGeomPlane is infinite
        # for physics but has no renderable surface of its own).
        visual = UsdGeom.Cube.Define(self.stage, path + "_visual")
        visual.CreateSizeAttr(1.0)
        UsdGeom.XformCommonAPI(visual).SetTranslate(Gf.Vec3d(0.0, 0.0, z - 0.05))
        UsdGeom.XformCommonAPI(visual).SetScale(Gf.Vec3f(size, size, 0.1))
        visual.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.36, 0.40)])
        return path

    def add_rigid_cube(self, path: str, size: float, position: tuple[float, float, float],
                       mass: float, color: tuple[float, float, float] = (0.85, 0.45, 0.12)) -> dict:
        from pxr import Gf, UsdGeom, UsdPhysics

        cube = UsdGeom.Cube.Define(self.stage, path)
        cube.CreateSizeAttr(size)
        cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(*position))
        prim = cube.GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim)
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass)
        return {"path": path, "size_m": size, "spawn_position_m": list(position), "mass_kg": mass}

    def add_static_box_group(self, root_path: str, world_position: tuple[float, float, float],
                             plates: list[dict], color: tuple[float, float, float] = (0.72, 0.56, 0.36)) -> dict:
        """Author a fixed multi-plate body: one Xform root, one collider Cube per plate.

        Each plate is a `UsdGeom.Cube` with `size = 1` scaled to its full extents, so
        the scale factor IS the dimension and nothing is scaled twice. Only
        `CollisionAPI` is applied: at S2 the box is static, so the root carries no
        `RigidBodyAPI` (a dynamic box is S4, and then exactly one rigid body goes on
        the root, never on the children).
        """
        from pxr import Gf, UsdGeom, UsdPhysics

        UsdGeom.Xform.Define(self.stage, "/World")
        root = UsdGeom.Xform.Define(self.stage, root_path)
        UsdGeom.XformCommonAPI(root).SetTranslate(Gf.Vec3d(*world_position))

        authored = []
        for plate in plates:
            path = f"{root_path}/{plate['name']}"
            cube = UsdGeom.Cube.Define(self.stage, path)
            cube.CreateSizeAttr(1.0)
            cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
            api = UsdGeom.XformCommonAPI(cube)
            api.SetTranslate(Gf.Vec3d(*plate["center_m"]))
            api.SetScale(Gf.Vec3f(*[float(v) for v in plate["size_m"]]))
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
            authored.append({"name": plate["name"], "path": path,
                             "intended_size_m": list(plate["size_m"]),
                             "intended_center_m": list(plate["center_m"])})
        return {"root_path": root_path, "world_position_m": list(world_position),
                "plates": authored, "rigid_body_on_root": False}

    def world_bbox(self, prim_path: str) -> dict | None:
        """World-space bounding box read back from the authored stage.

        Read-back goes through the composed transform, so an accidental second
        scale on an ancestor shows up here instead of being assumed away.
        """
        from pxr import Gf, Usd, UsdGeom

        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            return None
        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
        box = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if box.IsEmpty():
            return None
        lo, hi = box.GetMin(), box.GetMax()
        return {
            "min_m": [float(v) for v in lo],
            "max_m": [float(v) for v in hi],
            "size_m": [float(hi[i] - lo[i]) for i in range(3)],
            "center_m": [float((hi[i] + lo[i]) / 2.0) for i in range(3)],
        }

    def world_to_local(self, root_path: str, world_point) -> list[float]:
        """Express a world point in a prim's local frame (box local Z is what S2 judges)."""
        from pxr import Gf, Usd, UsdGeom

        xformable = UsdGeom.Xformable(self.stage.GetPrimAtPath(root_path))
        to_world = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        local = to_world.GetInverse().Transform(Gf.Vec3d(*[float(v) for v in world_point]))
        return [float(v) for v in local]

    def export_stage(self, path: str) -> str:
        """Flatten and save the authored stage, so the run keeps the asset it simulated."""
        self.stage.Export(path)
        return path

    def add_dome_light(self, intensity: float = 1200.0, path: str = "/World/DomeLight") -> str:
        from pxr import UsdLux

        light = UsdLux.DomeLight.Define(self.stage, path)
        light.CreateIntensityAttr(intensity)
        return path

    def add_distant_light(self, intensity: float = 3000.0, path: str = "/World/KeyLight") -> str:
        from pxr import Gf, UsdGeom, UsdLux

        light = UsdLux.DistantLight.Define(self.stage, path)
        light.CreateIntensityAttr(intensity)
        UsdGeom.XformCommonAPI(light).SetRotate(Gf.Vec3f(-40.0, 0.0, 35.0))
        return path

    # ---- read-back ------------------------------------------------------
    def rigid_view(self, path: str):
        from isaacsim.core.experimental.prims import RigidPrim

        return RigidPrim(path)

    @staticmethod
    def read_state(view) -> dict:
        """Pose + velocity of a single rigid body, in world frame, SI units.

        Orientation comes back from the tensor API as (w, x, y, z).
        """
        positions, orientations = view.get_world_poses()
        linear, angular = view.get_velocities()
        p = positions.numpy()[0]
        q = orientations.numpy()[0]
        lv = linear.numpy()[0]
        av = angular.numpy()[0]
        return {
            "position_m": [float(v) for v in p],
            "orientation_wxyz": [float(v) for v in q],
            "linear_velocity_mps": [float(v) for v in lv],
            "angular_velocity_radps": [float(v) for v in av],
        }

    @staticmethod
    def is_finite(state: dict) -> bool:
        for key in ("position_m", "orientation_wxyz", "linear_velocity_mps", "angular_velocity_radps"):
            for v in state[key]:
                if not math.isfinite(v):
                    return False
        return True

    # ---- rendering ------------------------------------------------------
    def add_camera(self, path: str, eye: tuple[float, float, float],
                   target: tuple[float, float, float],
                   up: tuple[float, float, float] = (0.0, 0.0, 1.0),
                   focal_length: float = 24.0) -> dict:
        """Author an explicit USD camera and return its pose, so the PNG has provenance."""
        from pxr import Gf, UsdGeom

        cam = UsdGeom.Camera.Define(self.stage, path)
        cam.CreateFocalLengthAttr(focal_length)
        cam.CreateClippingRangeAttr(Gf.Vec2f(0.01, 1000.0))

        look_at = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(*up))
        camera_to_world = look_at.GetInverse()
        xform = UsdGeom.Xformable(cam.GetPrim())
        xform.ClearXformOpOrder()
        xform.AddTransformOp().Set(camera_to_world)
        return {
            "camera_path": path,
            "eye_m": list(eye),
            "target_m": list(target),
            "up": list(up),
            "focal_length_mm": focal_length,
            "convention": "USD camera looks down -Z with +Y up in camera space",
        }

    def capture_rgb(self, camera_path: str, width: int = 1280, height: int = 720,
                    settle_frames: int = 48) -> dict:
        """Render one RGB frame offline via Replicator annotators.

        No timeline stepping happens here, so the image belongs to the final
        physics state, not to a rebuilt scene.
        """
        import omni.replicator.core as rep

        render_product = rep.create.render_product(camera_path, (width, height))
        annotator = rep.AnnotatorRegistry.get_annotator("rgb")
        annotator.attach([render_product])
        for _ in range(settle_frames):
            self.app.update()
        data = annotator.get_data()
        annotator.detach()
        try:
            render_product.destroy()
        except Exception:
            pass

        if data is None or getattr(data, "size", 0) == 0:
            return {"ok": False, "reason": "annotator returned no data", "width": width, "height": height}

        array = data  # (H, W, 4) uint8 RGBA
        h, w = int(array.shape[0]), int(array.shape[1])
        rgb = array[:, :, :3].tobytes()
        return {"ok": True, "width": w, "height": h, "channels": 3, "pixels": rgb,
                "settle_frames": settle_frames}
