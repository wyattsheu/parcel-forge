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


if __name__ == "__main__":
    unittest.main()
