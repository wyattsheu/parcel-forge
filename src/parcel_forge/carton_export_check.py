"""Open an exported carton USD and report which physics it actually carries.

Anyone can open the USD. What they get from the file alone is an articulated box with
elastic hinges. The creasing - the part that makes a fold permanent - is a per-step
Python rule, not a USD attribute, so it is listed here as absent rather than implied.
"""
import argparse,json,math
from pathlib import Path

FLAPS=['MajorYN','MajorYP','MinorXP','MinorXN']


def inspect(path,config):
    # PhysxSchema only registers once Kit is up; read its attributes by name instead.
    from pxr import Usd,UsdGeom,UsdPhysics
    stage=Usd.Stage.Open(str(path));report={'stage':str(path)}
    default=stage.GetDefaultPrim();report['default_prim']=default.GetPath().pathString if default else None
    scene=[p for p in stage.Traverse() if p.IsA(UsdPhysics.Scene)]
    report['physics_scene']=[{'path':p.GetPath().pathString,
                              'gravity_direction':list(UsdPhysics.Scene(p).GetGravityDirectionAttr().Get() or []),
                              'gravity_magnitude':UsdPhysics.Scene(p).GetGravityMagnitudeAttr().Get()} for p in scene]
    roots=[p.GetPath().pathString for p in stage.Traverse() if p.HasAPI(UsdPhysics.ArticulationRootAPI)]
    report['articulation_roots']=roots
    links=[]
    for prim in stage.Traverse():
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):continue
        mass=UsdPhysics.MassAPI(prim).GetMassAttr().Get() if prim.HasAPI(UsdPhysics.MassAPI) else None
        colliders=[c.GetPath().pathString for c in Usd.PrimRange(prim) if c.HasAPI(UsdPhysics.CollisionAPI)]
        links.append({'path':prim.GetPath().pathString,'mass_kg':mass,'colliders':colliders})
    report['rigid_bodies']=links
    joints=[]
    for name in FLAPS:
        prim=stage.GetPrimAtPath('/World/Carton/Hinge'+name)
        if not prim:continue
        joint=UsdPhysics.RevoluteJoint(prim);drive=UsdPhysics.DriveAPI(prim,'angular')
        entry={'path':prim.GetPath().pathString,'type':prim.GetTypeName(),
               'axis':joint.GetAxisAttr().Get(),
               'lower_limit_deg':joint.GetLowerLimitAttr().Get(),'upper_limit_deg':joint.GetUpperLimitAttr().Get(),
               'drive_type':drive.GetTypeAttr().Get(),
               'drive_stiffness_per_deg':drive.GetStiffnessAttr().Get(),
               'drive_damping_per_deg':drive.GetDampingAttr().Get(),
               'drive_target_deg':drive.GetTargetPositionAttr().Get(),
               'drive_max_force':drive.GetMaxForceAttr().Get(),
               'body0':[t.pathString for t in joint.GetBody0Rel().GetTargets()],
               'body1':[t.pathString for t in joint.GetBody1Rel().GetTargets()]}
        # Do not reuse `name` here: it is the flap being inspected.
        for label,attribute_name in [('physx_joint_friction','physxJoint:jointFriction'),
                                     ('staticFrictionEffort','physxJointAxis:angular:staticFrictionEffort'),
                                     ('dynamicFrictionEffort','physxJointAxis:angular:dynamicFrictionEffort')]:
            attribute=prim.GetAttribute(attribute_name)
            if attribute:entry[label]=attribute.Get()
        gains=config.get('crease_gains',{}).get(name)
        if gains and entry['drive_stiffness_per_deg']:
            entry['stiffness_nm_rad_from_usd']=entry['drive_stiffness_per_deg']*180/math.pi
            entry['matches_config']=math.isclose(entry['stiffness_nm_rad_from_usd'],gains['stiffness_nm_rad'],rel_tol=1e-5)
        joints.append(entry)
    report['revolute_joints']=joints
    report['in_the_usd']=['rigid bodies and their masses','collision geometry','one articulation root',
                          'four revolute creases with their axes and angle limits','angular drive stiffness, damping, rest angle and force limit',
                          'joint friction','gravity and the physics scene']
    report['not_in_the_usd']={
     'crease_yield_torque_nm':config.get('yield_torque_nm'),
     'plastic_viscosity_nm_s_rad':config.get('plastic_viscosity_nm_s_rad'),
     'softening_rate_per_rad':config.get('softening_rate_per_rad'),
     'why':'the drive rest angle is a single number in the USD; making a fold permanent means moving that number every physics step against a yield rule, which USD has no attribute for',
     'consequence':'opened with the USD alone, a flap is an elastic hinge: push it and it springs back to the authored rest angle. Run crease_controller/load_in_isaacsim.py to get the permanent creasing.',
     'panel_deformation':'not modelled at all: the panels are rigid, so the box cannot dent, crush or tear however hard it is hit'}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--package',required=True);args=parser.parse_args()
    package=Path(args.package);config=json.loads((package/'config.json').read_text())
    report=inspect(package/'carton.usda',config)
    (package/'physics_in_usd.json').write_text(json.dumps(report,indent=2)+'\n')
    ok=bool(report['articulation_roots']) and len(report['revolute_joints'])==4 and all(j.get('matches_config') for j in report['revolute_joints'])
    print('physics readback ok' if ok else 'physics readback INCOMPLETE')
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
