"""Rigid-panel carton USD authoring, no simulation or acceptance logic."""
import math

def author_carton(stage,config):
    from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema,UsdLux
    UsdGeom.Xform.Define(stage,'/World');carton=UsdGeom.Xform.Define(stage,'/World/Carton');stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    UsdPhysics.ArticulationRootAPI.Apply(carton.GetPrim());articulation_api=PhysxSchema.PhysxArticulationAPI.Apply(carton.GetPrim());articulation_api.CreateEnabledSelfCollisionsAttr(True)
    if 'solver_position_iterations' in config:
        articulation_api.CreateSolverPositionIterationCountAttr(config['solver_position_iterations']);articulation_api.CreateSolverVelocityIterationCountAttr(config['solver_velocity_iterations'])
    base=UsdGeom.Xform.Define(stage,'/World/Carton/Base');UsdPhysics.RigidBodyAPI.Apply(base.GetPrim());UsdPhysics.MassAPI.Apply(base.GetPrim()).CreateMassAttr(config.get('base_mass_kg',0.2))
    def plate(path,size,center):
        cube=UsdGeom.Cube.Define(stage,path);cube.CreateSizeAttr(1);api=UsdGeom.XformCommonAPI(cube);api.SetTranslate(Gf.Vec3d(*center));api.SetScale(Gf.Vec3f(*size));cube.CreateDisplayColorAttr([Gf.Vec3f(.58,.37,.18)]);UsdPhysics.CollisionAPI.Apply(cube.GetPrim());collision=PhysxSchema.PhysxCollisionAPI.Apply(cube.GetPrim());collision.CreateContactOffsetAttr(.001);collision.CreateRestOffsetAttr(0);return cube
    L,W,H,t=config['length_m'],config['width_m'],config['height_m'],config['thickness_m']
    plate('/World/Carton/Base/Bottom',(L,W,t),(0,0,t/2))
    for name,size,center in [('WallXP',(t,W,H),(L/2-t/2,0,H/2)),('WallXN',(t,W,H),(-L/2+t/2,0,H/2)),('WallYP',(L,t,H),(0,W/2-t/2,H/2)),('WallYN',(L,t,H),(0,-W/2+t/2,H/2))]:plate('/World/Carton/Base/'+name,size,center)
    # 'fixed' nails the box to the world, which is what the flap experiments wanted.
    # 'free' leaves it a body standing on the ground, which is what a robot cell needs:
    # it can then be pushed, and opening a flap may move it.
    if config.get('base_mode','fixed')=='fixed':
        fixed=UsdPhysics.FixedJoint.Define(stage,'/World/Carton/FixedBase');fixed.CreateBody1Rel().SetTargets([base.GetPath()])
    elif config.get('base_mode')!='free':raise ValueError("base_mode must be fixed or free")
    if config.get('ground_plane'):plate('/World/Ground',(3,3,.02),(0,0,-.01))
    f=W/2-config.get("flap_tip_clearance_m",0)
    # The crease axis sits on the wall's outer face, and the panel hangs on the outside
    # of it (local -t/2), so a flap folded right back to 270 deg lies flush against the
    # outside of the wall instead of sinking half a board into it. Hinge heights are one
    # board higher than the panel they carry, keeping majors stacked over minors shut.
    specs=[('MajorYN',L-2*t-2*config.get('flap_side_clearance_m',0),(0,-W/2,H+2*t),0),('MajorYP',L-2*t-2*config.get('flap_side_clearance_m',0),(0,W/2,H+2*t),180),('MinorXP',W-2*t-2*config.get('flap_side_clearance_m',0),(L/2,0,H+t),90),('MinorXN',W-2*t-2*config.get('flap_side_clearance_m',0),(-L/2,0,H+t),-90)]
    joints=[]
    for name,width,hinge,yaw in specs:
        link=UsdGeom.Xform.Define(stage,'/World/Carton/'+name);api=UsdGeom.XformCommonAPI(link);api.SetTranslate(Gf.Vec3d(*hinge));api.SetRotate(Gf.Vec3f(config.get('initial_angle_deg',0),0,yaw));UsdPhysics.RigidBodyAPI.Apply(link.GetPrim());mass=config['equivalent_density_kg_m3']*width*f*t;UsdPhysics.MassAPI.Apply(link.GetPrim()).CreateMassAttr(mass)
        plate(str(link.GetPath())+'/Panel',(width,f,t),(0,f/2,-t/2))
        joint=UsdPhysics.RevoluteJoint.Define(stage,'/World/Carton/Hinge'+name);joint.CreateBody0Rel().SetTargets([base.GetPath()]);joint.CreateBody1Rel().SetTargets([link.GetPath()]);joint.CreateAxisAttr('X');joint.CreateLocalPos0Attr(Gf.Vec3f(*hinge));joint.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));q=Gf.Rotation(Gf.Vec3d(0,0,1),yaw).GetQuat();joint.CreateLocalRot0Attr(Gf.Quatf(q));joint.CreateLocalRot1Attr(Gf.Quatf(1));joint.CreateLowerLimitAttr(config.get('crease_lower_limit_deg',-5));joint.CreateUpperLimitAttr(config.get('crease_upper_limit_deg',100))
        gains=config.get('crease_gains',{}).get(name,config)
        drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'angular');drive.CreateTypeAttr('force');drive.CreateStiffnessAttr(gains['stiffness_nm_rad']*math.pi/180);drive.CreateDampingAttr(gains['damping_nm_s_rad']*math.pi/180);drive.CreateTargetPositionAttr(0);drive.CreateMaxForceAttr(1)
        PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim()).CreateJointFrictionAttr(config['joint_friction_coefficient'])
        if 'crease_static_friction_nm' in config:
            joint.GetPrim().ApplyAPI('PhysxJointAxisAPI','angular')
            for key,field in [('crease_static_friction_nm','staticFrictionEffort'),('crease_dynamic_friction_nm','dynamicFrictionEffort')]:
                attr=joint.GetPrim().GetAttribute('physxJointAxis:angular:'+field)
                if not attr or not attr.Set(config[key]):raise RuntimeError('Installed schema cannot author angular friction effort')
        joints.append(joint)
    light=UsdLux.DomeLight.Define(stage,'/World/Light');light.CreateIntensityAttr(900)
    return joints,specs
