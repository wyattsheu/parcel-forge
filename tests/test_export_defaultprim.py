"""Regression test for the 2026-09-16 WebRTC-viewer bug.

Root cause: the human's known-good WebRTC viewer loads a USD file via a
*reference* (`stage.DefinePrim(...).GetReferences().AddReference(path)`), and USD
composition resolves an unqualified reference through the target layer's
`defaultPrim`. `Stage.Export()` does not set one on its own. Our S2 scene export
skipped this, so a fully-built scene (ground + box + probe) referenced into that
viewer resolved to nothing: "1 prims, 0 meshes, bbox 0x0x0, top-level prims = []".
The user saw only the viewer's own placeholder floor and reported "there's nothing
there but a floor" -- which was in fact exactly correct.

This needs `pxr`, which is not installed for the plain system Python that runs the
rest of this suite (see docs/DECISIONS.md D008). It is skipped there and must be
run with the Isaac venv interpreter to actually execute:

    /mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 -m unittest \\
        tests.test_export_defaultprim -v
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

try:
    from pxr import Usd, UsdGeom
    HAVE_PXR = True
except ImportError:
    HAVE_PXR = False


@unittest.skipUnless(HAVE_PXR, "pxr is only available under the Isaac venv interpreter (see D008)")
class TestDefaultPrimRequiredForReferences(unittest.TestCase):
    def _build_scene(self, path, set_default_prim):
        stage = Usd.Stage.CreateNew(path)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        world = UsdGeom.Xform.Define(stage, "/World")
        UsdGeom.Cube.Define(stage, "/World/Box")
        if set_default_prim:
            stage.SetDefaultPrim(world.GetPrim())
        stage.GetRootLayer().Save()

    def _reference_into_new_stage(self, referenced_path):
        """Reproduce exactly what the WebRTC viewer does: reference the file
        under a fresh prim in a new stage, with no explicit target path."""
        host = Usd.Stage.CreateInMemory()
        model = host.DefinePrim("/World/Model", "Xform")
        model.GetReferences().AddReference(referenced_path)
        return host, model

    def test_export_without_defaultprim_resolves_to_nothing(self):
        """This is the bug: a well-formed multi-prim stage becomes invisible."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "no_default.usda")
            self._build_scene(path, set_default_prim=False)
            host, model = self._reference_into_new_stage(path)
            children = list(host.Traverse())
            box_paths = [str(p.GetPath()) for p in children if p.GetPath().name == "Box"]
            self.assertEqual(box_paths, [],
                             "a reference without defaultPrim must resolve to no content "
                             "(this reproduces what the human's viewer showed)")

    def test_export_with_defaultprim_is_visible(self):
        """The fix: setting defaultPrim before export makes the reference resolve."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "with_default.usda")
            self._build_scene(path, set_default_prim=True)
            host, model = self._reference_into_new_stage(path)
            children = list(host.Traverse())
            box_paths = [str(p.GetPath()) for p in children if p.GetPath().name == "Box"]
            self.assertEqual(box_paths, ["/World/Model/Box"],
                             "with defaultPrim set, the referenced content must be reachable")

    def test_isaacsim_runtime_export_stage_sets_default_prim(self):
        """The actual fix, exercised without booting Kit: export_stage() must set
        defaultPrim on a stage that doesn't already have one."""
        from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

        with tempfile.TemporaryDirectory() as tmp:
            stage = Usd.Stage.CreateInMemory()
            UsdGeom.Xform.Define(stage, "/World")
            UsdGeom.Cube.Define(stage, "/World/Box")
            self.assertFalse(stage.HasDefaultPrim())

            runtime = IsaacSimRuntime.__new__(IsaacSimRuntime)  # bypass SimulationApp
            runtime.stage = stage
            out_path = os.path.join(tmp, "exported.usda")
            runtime.export_stage(out_path)

            self.assertTrue(stage.HasDefaultPrim())
            reopened = Usd.Stage.Open(out_path)
            self.assertTrue(reopened.HasDefaultPrim())
            self.assertEqual(str(reopened.GetDefaultPrim().GetPath()), "/World")


@unittest.skipUnless(HAVE_PXR, "pxr is only available under the Isaac venv interpreter (see D008)")
class TestPhysicsSceneReachableThroughReference(unittest.TestCase):
    """A root-level PhysicsScene is dropped by a reference, leaving rigid bodies
    with nothing to simulate against.

    Isaac authors its scene at `/PhysicsScene`, a sibling of `/World`. Since a
    reference only pulls in the default prim's subtree, the scene vanished and the
    probe sat frozen in mid-air. Measured before the fix: zero physics scenes in the
    referencing stage, probe unchanged at z=0.47000 after 3 s of stepping.
    """

    def _scene_with_root_level_physics(self, path):
        from pxr import UsdPhysics

        stage = Usd.Stage.CreateNew(path)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        world = UsdGeom.Xform.Define(stage, "/World")
        UsdGeom.Cube.Define(stage, "/World/Probe")
        UsdPhysics.Scene.Define(stage, "/PhysicsScene")  # sibling, not a child
        stage.SetDefaultPrim(world.GetPrim())
        stage.GetRootLayer().Save()

    def _referenced_physics_scenes(self, path):
        from pxr import UsdPhysics

        host = Usd.Stage.CreateInMemory()
        host.DefinePrim("/World/Model", "Xform").GetReferences().AddReference(path)
        return [str(p.GetPath()) for p in host.Traverse() if p.IsA(UsdPhysics.Scene)]

    def test_root_level_scene_is_lost_through_a_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "root_scene.usda")
            self._scene_with_root_level_physics(path)
            self.assertEqual(self._referenced_physics_scenes(path), [],
                             "a sibling PhysicsScene must not survive a reference "
                             "(this is the frozen-probe bug)")

    def test_relocation_makes_the_scene_reachable(self):
        from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "root_scene.usda")
            self._scene_with_root_level_physics(path)
            self.assertTrue(IsaacSimRuntime._relocate_physics_scene(path))
            self.assertEqual(self._referenced_physics_scenes(path),
                             ["/World/Model/PhysicsScene"])

    def test_relocation_leaves_exactly_one_scene(self):
        from pxr import UsdPhysics
        from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "root_scene.usda")
            self._scene_with_root_level_physics(path)
            IsaacSimRuntime._relocate_physics_scene(path)
            opened = Usd.Stage.Open(path)
            scenes = [str(p.GetPath()) for p in opened.Traverse() if p.IsA(UsdPhysics.Scene)]
            self.assertEqual(scenes, ["/World/PhysicsScene"],
                             "a direct open must not see two competing physics scenes")

    def test_relocation_is_a_no_op_when_already_inside(self):
        from pxr import UsdPhysics
        from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ok_scene.usda")
            stage = Usd.Stage.CreateNew(path)
            world = UsdGeom.Xform.Define(stage, "/World")
            UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
            stage.SetDefaultPrim(world.GetPrim())
            stage.GetRootLayer().Save()
            self.assertFalse(IsaacSimRuntime._relocate_physics_scene(path))


if __name__ == "__main__":
    unittest.main()
