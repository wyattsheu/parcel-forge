"""Directional strip proxy: D [Nm] -> rotational cell spring [Nm/rad]."""
import math

def stiffness(d_nm,width_m,pitch_m,half_cell=False):
    if not all(math.isfinite(x) and x>0 for x in (d_nm,width_m,pitch_m)):
        raise ValueError('positive finite material stiffness and dimensions required')
    return d_nm*width_m/pitch_m*(2 if half_cell else 1)

def add_joint(stage,path,body0,body1,pos0,k,axis='X'):
    from pxr import UsdPhysics,Gf
    j=UsdPhysics.RevoluteJoint.Define(stage,path)
    j.CreateBody0Rel().SetTargets([body0]);j.CreateBody1Rel().SetTargets([body1])
    j.CreateAxisAttr(axis);j.CreateLocalPos0Attr(Gf.Vec3f(*pos0));j.CreateLocalPos1Attr(Gf.Vec3f(0))
    j.CreateLowerLimitAttr(-30);j.CreateUpperLimitAttr(30)
    d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),'angular');d.CreateTypeAttr('force')
    d.CreateStiffnessAttr(k*math.pi/180);d.CreateDampingAttr(.02*math.pi/180)
    d.CreateTargetPositionAttr(0);d.CreateMaxForceAttr(10)
    return j

def author_segmented_carton(stage,config,material,n=4):
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
    from parcel_forge.carton_author import author_carton
    from parcel_forge.carton_feel import segment_stability
    # A board this stiff cut into light segments puts omega*dt far past 1 and the strips
    # buzz instead of holding the panel flat. Refuse to author that silently.
    policy=config.get('panel_stability_policy','require')
    if policy not in ('require','record'):raise ValueError("panel_stability_policy must be require or record")
    joints,specs=author_carton(stage,config);f=config['width_m']/2-config.get('flap_tip_clearance_m',0);h=f/n;roles={};stability={}
    for name,width,hinge,yaw in specs:
        direction=config['panel_directions'][name];k=stiffness(material['bending_stiffness_nm'][direction],width,h)
        segment_mass=material['areal_mass_kg_m2']*width*h
        stability[name]=dict(segment_stability(k,segment_mass*h*h/3,config['dt_s']),stiffness_nm_rad=k)
        if policy=='require' and not stability[name]['stable']:
            raise ValueError('segment drive omega*dt=%.1f exceeds the integrable limit for %s; use rigid panels or record the instability explicitly'%(stability[name]['omega_dt'],name))
        prev='/World/Carton/'+name
        for i in range(n):
            path='/World/Carton/'+name+('' if i==0 else '_S'+str(i))
            if i:
                link=UsdGeom.Xform.Define(stage,path);a=UsdGeom.XformCommonAPI(link)
                offset=Gf.Rotation(Gf.Vec3d(0,0,1),yaw).TransformDir(Gf.Vec3d(0,i*h,0))
                a.SetTranslate(Gf.Vec3d(*hinge)+offset);a.SetRotate(Gf.Vec3f(0,0,yaw))
                UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
                cube=UsdGeom.Cube.Define(stage,path+'/Panel');cube.CreateSizeAttr(1)
                cube.CreateDisplayColorAttr([Gf.Vec3f(.58,.37,.18)])
                UsdPhysics.CollisionAPI.Apply(cube.GetPrim());PhysxSchema.PhysxCollisionAPI.Apply(cube.GetPrim()).CreateContactOffsetAttr(.0002)
            cube=UsdGeom.Cube(stage.GetPrimAtPath(path+'/Panel'));a=UsdGeom.XformCommonAPI(cube)
            a.SetScale(Gf.Vec3f(width,h,material['thickness_m']));a.SetTranslate(Gf.Vec3d(0,h/2,0))
            UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(path)).CreateMassAttr(material['areal_mass_kg_m2']*width*h)
            if i:
                jname='Bend'+name+'_'+str(i)
                add_joint(stage,'/World/Carton/'+jname,prev,path,(0,h,0),k)
                roles[jname]={'stiffness_nm_rad':k,'direction':direction}
            prev=path
    stage.GetPrimAtPath('/World/Carton').SetCustomDataByKey('parcelForge:constitutiveModel',config.get('panel_constitutive_model','elastic_strip_v1'))
    stage.GetPrimAtPath('/World/Carton').SetCustomDataByKey('parcelForge:materialConfig','config.json')
    config['panel_bend_joints']=roles;config['panel_model']='segmented_directional_strip_v1';config['panel_stability']=stability
    return joints,specs
