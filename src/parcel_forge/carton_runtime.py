"""Four rigid RSC flaps and stateful crease controller on installed Isaac 6."""
import argparse,csv,json,math,traceback
from pathlib import Path
from parcel_forge.crease_model import CreaseState,advance

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
    config=json.loads((out/'config.json').read_text());dt=config['dt_s']
    from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
    r=IsaacSimRuntime(dt=dt,device=config.get('physics_device','cuda:0'),enable_cameras=False)
    def progress(event,**fields):
        with (out/'progress.jsonl').open('a') as file:
            file.write(json.dumps({'event':event,**fields})+'\n');file.flush()
    progress('runtime_requested',scenario=config.get('scenario','legacy-mixed'))
    result={'status':'failed','physics':'not_tested','render':'not_tested','webrtc_human_view':'not_tested','material_calibration':'not_tested'}
    try:
        r.start();result['runtime']=r.configure_physics(gravity=9.81,enable_ccd=False)
        from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema,UsdLux
        from parcel_forge.carton_author import author_carton
        stage=r.stage;joints,specs=author_carton(stage,config)
        stage.GetRootLayer().Export(str(out/'asset.usda'));progress('asset_generated',asset='asset.usda')
        r.play()
        from isaacsim.core.experimental.prims import Articulation
        view=Articulation('/World/Carton');r.step(2)
        result['mass_readback']=view.get_link_masses().numpy().tolist()
        result['inertia_readback']=view.get_link_inertias().numpy().tolist()
        if 'crease_static_friction_nm' in config:
            friction=view.get_dof_friction_properties();result['friction_readback']=[v.numpy().tolist() for v in friction]
            for i,key in enumerate(['crease_static_friction_nm','crease_dynamic_friction_nm']):
                if any(not math.isclose(float(x),config[key],abs_tol=1e-7) for x in friction[i].numpy()[0]):raise RuntimeError('Angular friction readback mismatch')
        result['drive_readback']=[v.numpy().tolist() for v in view.get_dof_gains()]
        names=view.dof_names;result['dof_names']=names
        if len(names)!=4:raise RuntimeError('Expected four articulation DOFs')
        from isaacsim.core.experimental.prims import RigidPrim
        links={name:RigidPrim('/World/Carton/'+name) for name,_,_,_ in specs}
        progress('physics_readback_ready',dof_names=names)
        states=[CreaseState() for _ in names];rows=[];pose_rows=[];peak=[0]*4;maxplastic=[0]*4
        # Equal outward torque on three flaps; one low-torque control. No pose forcing.
        low_index=names.index('HingeMajorYN');last_drive_targets=None
        for step in range(round(config['duration_s']/dt)):
            theta=view.get_dof_positions().numpy()[0];velocity=view.get_dof_velocities().numpy()[0]
            targets=[];efforts=[];time=step*dt
            if step%round(3/dt)==0:progress('physics_running',step=step,time_s=time)
            if step%max(1,round(1/(30*dt)))==0:
                for link_name,link in links.items():
                    positions,orientations=link.get_world_poses();pose_rows.append([time,link_name,*map(float,positions.numpy()[0]),*map(float,orientations.numpy()[0])])
            for i,name in enumerate(names):
                state,info=advance(states[i],float(theta[i]),dt,config['stiffness_nm_rad'],config['yield_torque_nm'],config['plastic_viscosity_nm_s_rad'],config['softening_rate_per_rad']);states[i]=state;targets.append(state.target)
                torque=(config['low_applied_torque_nm'] if i==low_index else config['high_applied_torque_nm']) if time<config['load_duration_s'] else 0.0;
                if config.get('scenario') in ['opening-order','crease-coupon','crease-cyclic']:
                    profile=config['opening_profile'];major='Major' in name
                    if major and time<profile['major_loading_end_s']:torque=config['high_applied_torque_nm']
                    elif major and (time<profile['minor_loading_end_s'] or config.get('scenario') in ['crease-coupon','crease-cyclic']):torque=config['stiffness_nm_rad']*(profile['major_hold_angle_rad']-state.target)
                    elif not major and profile['major_loading_end_s']<=time<profile['minor_loading_end_s']:torque=config['high_applied_torque_nm']
                    else:torque=0.0
                    if config.get('scenario') in ['crease-coupon','crease-cyclic'] and name=='HingeMinorXP' and profile['major_loading_end_s']<=time<profile['minor_loading_end_s']:torque=config['low_applied_torque_nm']
                if config.get('scenario')=='crease-cyclic' and not major:
                        opening=any(start<=time<end for start,end in config['cycle_profile']['opening_intervals_s']);closing=any(start<=time<end for start,end in config['cycle_profile']['closing_intervals_s'])
                        torque=(config['low_applied_torque_nm'] if name=='HingeMinorXP' else config['high_applied_torque_nm']) if opening else (-config['high_applied_torque_nm'] if closing and name=='HingeMinorXN' else 0.0)
                efforts.append(torque)
                rows.append([step,time,name,float(theta[i]),float(velocity[i]),state.target,info['trial_elastic_torque_nm'],info['yield_torque_nm'],info['plastic_increment_rad'],torque]);peak[i]=max(peak[i],float(theta[i]));maxplastic[i]=max(maxplastic[i],abs(state.target))
            # Offset the force-drive reference to impose the known loading torque:
            # k*(p+Mext/k-theta)-c*v == -k*(theta-p)-c*v+Mext.
            # Plastic state is p, not the temporary actuator offset. No pose teleport.
            drive_targets=[targets[i]+efforts[i]/config['stiffness_nm_rad'] for i in range(4)]
            if drive_targets!=last_drive_targets:
                view.set_dof_position_targets([drive_targets]);last_drive_targets=drive_targets
            result['loading_method']='force-drive reference offset equivalent to prescribed additive torque; no pose forcing'
            r.step()
        final=view.get_dof_positions().numpy()[0];vel=view.get_dof_velocities().numpy()[0]
        for joint in joints:
            index=names.index(joint.GetPrim().GetName());UsdPhysics.DriveAPI(joint.GetPrim(),'angular').GetTargetPositionAttr().Set(math.degrees(states[index].target))
        # Bake tensor-measured link poses; physics USD writeback need not be enabled.
        from isaacsim.core.experimental.prims import RigidPrim
        for name,_,_,_ in specs:
            positions,orientations=RigidPrim('/World/Carton/'+name).get_world_poses();pos=positions.numpy()[0];quat=orientations.numpy()[0];xform=UsdGeom.Xformable(stage.GetPrimAtPath('/World/Carton/'+name));xform.ClearXformOpOrder();xform.AddTranslateOp().Set(Gf.Vec3d(*map(float,pos)));xform.AddOrientOp().Set(Gf.Quatf(float(quat[0]),Gf.Vec3f(*map(float,quat[1:]))))
        stage.GetRootLayer().Export(str(out/'scene_final.usda'))
        with (out/'trajectory.csv').open('w') as file:
            writer=csv.writer(file);writer.writerow(['step','time_s','joint','angle_rad','velocity_rad_s','plastic_target_rad','trial_elastic_torque_nm','yield_torque_nm','plastic_increment_rad','applied_torque_nm']);writer.writerows(rows)
        with (out/'link_poses.csv').open('w') as file:
            writer=csv.writer(file);writer.writerow(['time_s','link','px','py','pz','qw','qx','qy','qz']);writer.writerows(pose_rows)
        from parcel_forge.carton_recording import export_recording
        result['recording']=export_recording(out)
        result.update(physics='pass',samples=len(rows),flaps=[{'joint':name,'peak_deg':math.degrees(peak[i]),'final_deg':math.degrees(float(final[i])),'final_velocity_rad_s':float(vel[i]),'plastic_target_deg':math.degrees(states[i].target),'accumulated_plastic_rad':states[i].accumulated_plastic} for i,name in enumerate(names)])
        from parcel_forge.validation.carton import evaluate_carton
        result.update(evaluate_carton(config,names,rows,peak,maxplastic,states,final,vel))
    except Exception as exc:result['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        progress('finished',status=result['status'],opening=result.get('opening_diagnostic_status','not_tested'),coupon=result.get('coupon_diagnostic_status','not_tested'),cyclic=result.get('cyclic_diagnostic_status','not_tested'))
        (out/'carton_result.json').write_text(json.dumps(result,indent=2)+'\n');r.close()
    return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
