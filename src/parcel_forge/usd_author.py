"""Author an open-box asset as a clean, self-contained USD layer.

Needs `pxr`, which on this machine lives inside the Isaac runtime, but NOT Kit:
`from pxr import Usd` costs about 2.6 s and no GPU, so building and validating
assets never occupies the simulator (see D008).

The asset written here is deliberately not a simulation scene: no ground plane,
no lights, no PhysicsScene. Those belong to the test world, so one asset can be
dropped into many different tests (handbook section 7).
"""

from __future__ import annotations

from .geometry import geometry_manifest
from .mass_properties import mass_manifest

ASSET_ROOT = "/OpenBox"


def author_open_box(usd_path: str, outer_size_m, wall_thickness_m, fault: str = "none",
                    body_mode: str = "static", shell_mass_kg: float | None = None,
                    asset_id: str = "open_box", display_color=(0.72, 0.56, 0.36)) -> dict:
    """Write the asset and return the manifest describing what was written."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    geom = geometry_manifest(outer_size_m, wall_thickness_m, fault)

    stage = Usd.Stage.CreateNew(usd_path)
    # Units and axis are declared explicitly: physics numbers are meaningless
    # without them, and OpenUSD's default length unit is not metres.
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)

    root = UsdGeom.Xform.Define(stage, ASSET_ROOT)
    stage.SetDefaultPrim(root.GetPrim())
    root.GetPrim().SetAssetInfoByKey("name", asset_id)
    Usd.ModelAPI(root.GetPrim()).SetKind("component")

    mass = None
    if body_mode == "dynamic":
        # Exactly one rigid body, on the root. The plates stay plain colliders:
        # a rigid body per plate would turn one box into five loose sheets.
        UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
        if shell_mass_kg is None:
            raise ValueError("dynamic body requires shell_mass_kg")
        mass = mass_manifest(outer_size_m, wall_thickness_m, shell_mass_kg, fault)
        mass_api = UsdPhysics.MassAPI.Apply(root.GetPrim())
        mass_api.CreateMassAttr(float(mass["total_mass_kg"]))
        mass_api.CreateCenterOfMassAttr(Gf.Vec3f(*mass["center_of_mass_local_m"]))
        mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*mass["principal_moments_kg_m2"]))
        qw, qx, qy, qz = mass["principal_axes_quaternion_wxyz"]
        mass_api.CreatePrincipalAxesAttr(Gf.Quatf(qw, Gf.Vec3f(qx, qy, qz)))

    authored = []
    for plate in geom["plates"]:
        path = f"{ASSET_ROOT}/{plate['name']}"
        cube = UsdGeom.Cube.Define(stage, path)
        # size = 1 with the scale carrying the real extents, so the scale factor
        # IS the dimension and nothing is scaled twice.
        cube.CreateSizeAttr(1.0)
        cube.CreateDisplayColorAttr([Gf.Vec3f(*display_color)])
        api = UsdGeom.XformCommonAPI(cube)
        api.SetTranslate(Gf.Vec3d(*[float(v) for v in plate["center_m"]]))
        api.SetScale(Gf.Vec3f(*[float(v) for v in plate["size_m"]]))
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        authored.append({"name": plate["name"], "path": path,
                         "size_m": list(plate["size_m"]), "center_m": list(plate["center_m"])})

    stage.GetRootLayer().Save()

    manifest = dict(geom)
    manifest.update({
        "asset_id": asset_id,
        "usd_path": usd_path,
        "default_prim": ASSET_ROOT,
        "body_mode": body_mode,
        "shell_mass_kg": shell_mass_kg,
        "stage_metadata": {"metersPerUnit": 1.0, "kilogramsPerUnit": 1.0, "upAxis": "Z"},
        "authored_prims": authored,
        "rigid_body_count_expected": 1 if body_mode == "dynamic" else 0,
        "mass_properties": mass,
    })
    return manifest
