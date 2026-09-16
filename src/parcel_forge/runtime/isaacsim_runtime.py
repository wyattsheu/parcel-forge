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

    def configure_physics(self, gravity: float = -9.81, enable_ccd: bool = True) -> dict:
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
        # Per-body CCD does nothing unless the scene enables it too.
        physx.CreateEnableCCDAttr(bool(enable_ccd))
        read_back = {
            "physics_scene_path": str(scene_prim.GetPath()),
            "gravity_direction": list(scene.GetGravityDirectionAttr().Get()),
            "gravity_magnitude": float(scene.GetGravityMagnitudeAttr().Get()),
            "dt_readback": float(self._sim.get_physics_dt()),
            "device_readback": str(self._sim.get_device()),
            "solver_type": physx.GetSolverTypeAttr().Get(),
            "gpu_dynamics": physx.GetEnableGPUDynamicsAttr().Get(),
            "ccd_enabled": physx.GetEnableCCDAttr().Get(),
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
                         z: float = 0.0, visual_size: float | None = None) -> str:
        """Infinite physics plane plus a proportionate visible slab.

        `size` drives the collider; `visual_size` drives what a camera sees. They
        are separate because the collision plane may as well be large, while an
        oversized visual slab swallows the frame in any viewer that auto-frames on
        the model (a 20 m slab next to a 0.3 m box fills the screen with grey).
        """
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
        extent = float(visual_size if visual_size is not None else size)
        visual = UsdGeom.Cube.Define(self.stage, path + "_visual")
        visual.CreateSizeAttr(1.0)
        UsdGeom.XformCommonAPI(visual).SetTranslate(Gf.Vec3d(0.0, 0.0, z - 0.005))
        UsdGeom.XformCommonAPI(visual).SetScale(Gf.Vec3f(extent, extent, 0.01))
        visual.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.36, 0.40)])
        return path

    def add_rigid_cube(self, path: str, size: float, position: tuple[float, float, float],
                       mass: float, color: tuple[float, float, float] = (0.85, 0.45, 0.12),
                       enable_ccd: bool = True) -> dict:
        """A dynamic cube. CCD is on by default, and that is a correctness fix.

        Discrete collision only samples position once per substep. The probe reaches
        about 2.2 m/s before contact, which is 3.7 cm of travel per step at
        dt = 1/60, against a 5 mm bottom plate: it passes straight through and lands
        on the world floor. Measured at 1/60 (z = 0.02000, tunnelled) versus 1/240
        (z = 0.22500, correct) -- see D017. Continuous collision detection sweeps the
        swept volume instead of sampling, so thin plates stop the probe regardless
        of timestep.
        """
        from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics

        cube = UsdGeom.Cube.Define(self.stage, path)
        cube.CreateSizeAttr(size)
        cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(*position))
        prim = cube.GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim)
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass)

        physx_body = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        physx_body.CreateEnableCCDAttr(bool(enable_ccd))

        return {"path": path, "size_m": size, "spawn_position_m": list(position),
                "mass_kg": mass, "ccd_enabled": bool(enable_ccd)}

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

    def set_prim_transform(self, prim_path: str, position, orientation_wxyz=None) -> None:
        """Write a measured pose into USD as a single transform op.

        PhysX publishes results through Fabric; it does not write them back to USD.
        Anything that renders from USD -- including the human's WebRTC viewer, which
        is launched with `useFabricSceneDelegate=0` -- therefore shows a body frozen
        at its authored spawn pose no matter how long physics runs. Measured:
        after 3 s the tensor API reported the probe at z=0.22500 while USD still
        read 0.47000.

        This writes the pose that was actually measured during the run, so a viewer
        can show the verified end state. It is a record of a real result, not a
        re-staged scene: the numbers come straight from trajectory.csv.
        """
        from pxr import Gf, UsdGeom

        prim = self.stage.GetPrimAtPath(prim_path)
        matrix = Gf.Matrix4d(1.0)
        if orientation_wxyz is not None:
            w, x, y, z = (float(v) for v in orientation_wxyz)
            matrix.SetRotate(Gf.Quatd(w, Gf.Vec3d(x, y, z)))
        matrix.SetTranslateOnly(Gf.Vec3d(*[float(v) for v in position]))

        xformable = UsdGeom.Xformable(prim)
        xformable.ClearXformOpOrder()
        xformable.AddTransformOp().Set(matrix)

    def export_stage(self, path: str, default_prim_path: str = "/World") -> str:
        """Flatten and save the authored stage, so the run keeps the asset it simulated.

        `Stage.Export()` does not set defaultPrim on its own. Any external tool that
        loads this file via a USD *reference* (rather than opening it directly) needs
        defaultPrim set, or the reference resolves to nothing -- this was found by
        the human's WebRTC viewer reporting "0 meshes, bbox 0x0x0, top-level prims =
        []" against a scene that in fact contained a full box+ground+probe setup.
        """
        from pxr import Sdf, Usd, UsdPhysics

        if not self.stage.HasDefaultPrim():
            root = self.stage.GetPrimAtPath(default_prim_path)
            if root and root.IsValid():
                self.stage.SetDefaultPrim(root)
        self.stage.Export(path)
        self._relocate_physics_scene(path)
        return path

    @staticmethod
    def _relocate_physics_scene(path: str) -> bool:
        """Move the PhysicsScene under the default prim in the exported file.

        Isaac authors the scene at root level (`/PhysicsScene`), a sibling of
        `/World`. A USD reference only pulls in the default prim's subtree, so a
        root-level scene is dropped and the referenced rigid bodies have nothing to
        simulate against: they sit frozen in mid-air. Verified by loading the file
        the way the human's viewer does -- the probe stayed at z=0.47000 for a full
        three seconds of stepping, and the referencing stage reported zero physics
        scenes. Creating a replacement scene after the fact does not rescue the
        already-referenced bodies, so the file itself has to carry one.

        This edits the exported layer only. The live simulation stage is untouched,
        so adding a second scene can never disturb a run in progress.
        """
        from pxr import Sdf, Usd, UsdPhysics

        layer = Sdf.Layer.FindOrOpen(path)
        if layer is None:
            return False
        stage = Usd.Stage.Open(layer)
        default_prim = stage.GetDefaultPrim()
        if not default_prim or not default_prim.IsValid():
            return False

        root_path = default_prim.GetPath()
        scenes = [prim.GetPath() for prim in stage.Traverse() if prim.IsA(UsdPhysics.Scene)]
        if not scenes:
            return False
        if any(scene_path.HasPrefix(root_path) and scene_path != root_path for scene_path in scenes):
            return False  # already reachable through the reference

        source = scenes[0]
        destination = root_path.AppendChild(source.name)
        if not Sdf.CopySpec(layer, source, layer, destination):
            return False
        # Leave exactly one scene behind, or a direct open sees two.
        if source.IsRootPrimPath():
            del layer.rootPrims[source.name]
        layer.Save()
        return True

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
