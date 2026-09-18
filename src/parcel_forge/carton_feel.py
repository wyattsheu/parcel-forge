"""Why a flap feels wrong: analytic hinge/panel diagnostics and parameter derivation.

Pure maths on a config, no simulator. Every quantity here is something a person can
check against a real box with a kitchen scale and a protractor, which is the point:
the numbers below are what the user is feeling when the flap will not stay folded.
"""
import math

G=9.81


def flap_geometry(config,flap='MajorYN'):
    """Lever arm, mass and self-weight torque of one flap about its crease."""
    L,W,t=config['length_m'],config['width_m'],config['thickness_m']
    lever=W/2-config.get('flap_tip_clearance_m',0)
    side=config.get('flap_side_clearance_m',0)
    width=(L if flap.startswith('Major') else W)-2*t-2*side
    material=config.get('material')
    mass=material['areal_mass_kg_m2']*width*lever if material else config['equivalent_density_kg_m3']*width*lever*t
    return {'flap':flap,'width_m':width,'lever_m':lever,'mass_kg':mass,
            'weight_n':mass*G,'weight_torque_nm':mass*G*lever/2,
            'inertia_about_crease_kg_m2':mass*lever*lever/3}


def crease_feel(config,geometry,open_angle_deg=90.):
    """Turn hinge gains into forces and angles a hand can feel at the flap tip."""
    k=config['stiffness_nm_rad'];yield_torque=config['yield_torque_nm'];eta=config['plastic_viscosity_nm_s_rad']
    lever=geometry['lever_m'];weight=geometry['weight_torque_nm']
    upper=math.radians(config.get('crease_upper_limit_deg',config.get('upper_limit_deg',100)))
    yield_angle=yield_torque/k
    torque_at_open=k*math.radians(open_angle_deg)
    return {
     'yield_angle_deg':math.degrees(yield_angle),
     'springback_after_creasing_deg':math.degrees(yield_angle),
     'tip_force_to_start_creasing_n':yield_torque/lever,
     'tip_force_to_keep_folding_n':yield_torque/lever,
     'tip_force_if_purely_elastic_to_open_n':torque_at_open/lever,
     'residual_torque_nm':yield_torque,
     'residual_over_self_weight':yield_torque/weight,
     'droops_under_own_weight':yield_torque<weight,
     'max_plastic_rate_rad_s':(max(0.,k*(upper-yield_angle)-yield_torque)/eta) if eta>0 else math.inf,
     'seconds_to_crease_45_deg_at_full_load':(math.radians(45)/((max(0.,k*(upper-yield_angle)-yield_torque)/eta)) if eta>0 and k*(upper-yield_angle)>yield_torque else math.inf),
     'plastic_rate_depends_on_pull_force':eta<=0,
     'hinge_omega_dt':math.sqrt(k/geometry['inertia_about_crease_kg_m2'])*config['dt_s']}


def derive_crease(geometry,springback_deg=4.,residual_over_self_weight=1.8,plastic_time_s=.02):
    """Pick hinge gains from two things a person can observe on a real carton:
    how far a creased flap springs back, and whether it holds its own weight."""
    if not 0<springback_deg<45 or residual_over_self_weight<=0 or plastic_time_s<=0:
        raise ValueError('springback in (0,45) deg, positive weight ratio and plastic time required')
    yield_torque=residual_over_self_weight*geometry['weight_torque_nm']
    stiffness=yield_torque/math.radians(springback_deg)
    return {'stiffness_nm_rad':stiffness,'yield_torque_nm':yield_torque,
            'plastic_viscosity_nm_s_rad':stiffness*plastic_time_s,
            'damping_nm_s_rad':.6*2*math.sqrt(stiffness*geometry['inertia_about_crease_kg_m2']),
            'provenance':'uncalibrated_assumption derived from target springback and self-weight ratio, not measured cardboard'}


def segment_stability(stiffness_nm_rad,inertia_kg_m2,dt_s,limit=.3):
    """An explicit drive is only integrable while omega*dt stays small.

    A stiff board split into light segments puts omega*dt far past 1, and PhysX then
    makes the strips buzz and fling apart instead of holding the panel flat.
    """
    if min(stiffness_nm_rad,inertia_kg_m2,dt_s,limit)<=0:raise ValueError('positive stiffness, inertia, dt and limit required')
    omega=math.sqrt(stiffness_nm_rad/inertia_kg_m2)
    return {'omega_rad_s':omega,'omega_dt':omega*dt_s,'stable':omega*dt_s<=limit,
            'max_stable_stiffness_nm_rad':inertia_kg_m2*(limit/dt_s)**2,'limit':limit}


def report(config,flap='MajorYN'):
    geometry=flap_geometry(config,flap);feel=crease_feel(config,geometry)
    out={'geometry':geometry,'crease':feel}
    bends=config.get('panel_bend_joints') or {}
    if bends:
        n=config.get('panel_segments',4);pitch=geometry['lever_m']/n
        segment_mass=geometry['mass_kg']/n;inertia=segment_mass*pitch*pitch/3
        name=next(iter(k for k in bends if flap in k),None)
        if name:out['panel_segment']=dict(segment_stability(bends[name]['stiffness_nm_rad'],inertia,config['dt_s']),
                                          joint=name,stiffness_nm_rad=bends[name]['stiffness_nm_rad'],
                                          inertia_kg_m2=inertia,crease_stiffness_ratio=bends[name]['stiffness_nm_rad']/config['stiffness_nm_rad'])
    return out


def derive_carton_creases(config,springback_deg=4.,residual_over_self_weight=1.5,plastic_time_s=.02):
    """Per-flap hinge gains. Crease stiffness and yield scale with crease length, so
    every flap springs back by the same angle and carries the same multiple of its
    own weight regardless of how wide it is."""
    flaps=['MajorYN','MajorYP','MinorXP','MinorXN'];gains={}
    for flap in flaps:
        geometry=flap_geometry(config,flap)
        derived=derive_crease(geometry,springback_deg,residual_over_self_weight,plastic_time_s)
        gains[flap]=dict(derived,width_m=geometry['width_m'],weight_torque_nm=geometry['weight_torque_nm'],
                         tip_force_to_start_creasing_n=derived['yield_torque_nm']/geometry['lever_m'])
    reference=flap_geometry(config,'MajorYN')
    return {'crease_gains':gains,
            'crease_stiffness_nm_rad_per_m':gains['MajorYN']['stiffness_nm_rad']/reference['width_m'],
            'crease_yield_nm_per_m':gains['MajorYN']['yield_torque_nm']/reference['width_m'],
            'crease_targets':{'springback_deg':springback_deg,'residual_over_self_weight':residual_over_self_weight,'plastic_time_s':plastic_time_s},
            'crease_provenance':'uncalibrated_assumption; targets chosen to match how a real flap behaves by hand, then to be replaced by a measured force-angle trace'}


def grab_force_table(config,flap='MajorYN',fractions=(1.,.75,.5,.25)):
    """What a hand (or a mouse grab) must deliver, depending on where it grabs.

    The crease resists with its yield torque and the flap also carries its own weight,
    so the force needed is that torque divided by the distance from the crease to the
    grabbed point. Grabbing halfway up the flap doubles the force needed.
    """
    geometry=flap_geometry(config,flap)
    gains=config.get('crease_gains',{}).get(flap,config)
    torque=gains['yield_torque_nm']+geometry['weight_torque_nm']
    rows=[]
    for fraction in fractions:
        if not 0<fraction<=1:raise ValueError('grab fractions must be in (0,1]')
        radius=geometry['lever_m']*fraction
        rows.append({'grab_fraction_of_flap':fraction,'radius_m':radius,'force_n':torque/radius,
                     'force_gram_force':torque/radius/G*1000})
    return {'flap':flap,'torque_to_start_opening_nm':torque,'crease_yield_nm':gains['yield_torque_nm'],
            'self_weight_torque_nm':geometry['weight_torque_nm'],'by_grab_point':rows,
            'note':'a closed flap must overcome its crease yield plus its own weight; measured opening force on this asset was 0.16 N at the tip'}
