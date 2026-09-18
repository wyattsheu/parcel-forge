"""Pull a flap like a hand does and measure what a real carton would do.

Rigid panels, all compliance at the creases, external forces only: no open/close
command exists in this asset. Every number here is measured from the run, and the
crease gains are derived targets, not calibrated cardboard.
"""
import argparse,csv,json,math,traceback
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.carton_feel import derive_carton_creases,report as feel_report

FLAPS=['MajorYN','MajorYP','MinorXP','MinorXN']


def board_mass(config):
    """Bottom plus four walls, from the board's areal mass."""
    L,W,H=config['length_m'],config['width_m'],config['height_m']
    return config['material']['areal_mass_kg_m2']*(L*W+2*L*H+2*W*H)


def build_config(root,springback_deg,residual_ratio,dt,base_mode='fixed'):
    material=json.loads((root/'config/materials/b_flute_130tl.json').read_text())
    config={'length_m':.30,'width_m':.20,'height_m':.15,'thickness_m':material['thickness_m'],
            'equivalent_density_kg_m3':material['areal_mass_kg_m2']/material['thickness_m'],
            'dt_s':dt,'flap_tip_clearance_m':.0005,'flap_side_clearance_m':.004,
            'softening_rate_per_rad':.15,'joint_friction_coefficient':0,
            # A real RSC flap folds right back against the outside of the wall. The
            # crease is authored on that outer face, so 180 deg lays the flap flat on
            # it; the old 100 deg limit was an arbitrary stop that jammed the carton
            # half open. The last degree is left out to avoid the degenerate flat pose.
            'crease_lower_limit_deg':-5,'crease_upper_limit_deg':270,
            'crease_static_friction_nm':.002,'crease_dynamic_friction_nm':.002,
            'solver_position_iterations':32,'solver_velocity_iterations':8,
            'material':material,'panel_model':'rigid_panel_v1','interaction_mode':'external_forces_only',
            'panel_model_reason':'the board is far stiffer than its creases, and a segmented strip of it cannot be integrated at this timestep; the panel is therefore rigid and every degree of freedom lives in a crease',
            'provenance':'uncalibrated_assumption'}
    config.update(base_mode=base_mode,ground_plane=base_mode=='free')
    config['base_mass_kg']=board_mass(config)
    config.update(derive_carton_creases(config,springback_deg,residual_ratio))
    reference=config['crease_gains']['MajorYN']
    config.update(stiffness_nm_rad=reference['stiffness_nm_rad'],yield_torque_nm=reference['yield_torque_nm'],
                  plastic_viscosity_nm_s_rad=reference['plastic_viscosity_nm_s_rad'],damping_nm_s_rad=reference['damping_nm_s_rad'])
    return config


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--springback-deg',type=float,default=4.)
    parser.add_argument('--residual-over-weight',type=float,default=1.5)
    parser.add_argument('--base',choices=['fixed','free'],default='fixed');args=parser.parse_args()
    out=Path(args.out);root=Path(__file__).resolve().parents[2];dt=1/240
    config=build_config(root,args.springback_deg,args.residual_over_weight,dt,args.base)
    result={'status':'fail','physics':'not_tested','render':'not_tested','human_webrtc':'not_tested','material_calibration':'not_tested'}
    runtime=IsaacSimRuntime(dt=dt,device='cpu',enable_cameras=False);controller=None;samples=[]
    try:
        runtime.start()
        from isaacsim.core.experimental.prims import RigidPrim
        from parcel_forge.carton_author import author_carton
        author_carton(runtime.stage,config)
        result['runtime']=runtime.configure_physics(gravity=9.81,enable_ccd=False)
        runtime.stage.GetRootLayer().Export(str(out/'asset.usda'));(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
        result['feel']=feel_report(config)
        from parcel_forge.carton_live import LiveCarton
        controller=LiveCarton(config);controller.show_controls();probe=controller.force_probe
        runtime.play();runtime.step(4)
        elapsed=[0.]
        def angles():return {n.replace('Hinge',''):math.degrees(float(v)) for n,v in zip(controller.names,controller.view.get_dof_positions().numpy()[0])}
        def run(seconds,note,force_n=0.):
            for _ in range(round(seconds/dt)):
                runtime.step();elapsed[0]+=dt
                samples.append([elapsed[0],note,force_n]+[angles()[f] for f in FLAPS])
            return angles()
        def peak(note,flap):
            index=FLAPS.index(flap)+3
            return max((row[index] for row in samples if row[1]==note),default=0.)
        phases={};phases['rest']=run(.5,'rest');flaps_tested=config['base_mode']=='fixed'

        if flaps_tested:
            # C then F: the user's report, run while every other flap is still closed so
            # nothing can block the returning flap. Open one flap, then push it shut again:
            # a real carton keeps the new fold instead of springing open.
            probe.apply('MajorYP',1.,.4);phases['quick_pull']=run(.4,'quick_pull',1.)
            probe.release();phases['quick_pull_released']=run(2.5,'quick_pull_release')
            press_before=math.degrees(controller.states['HingeMajorYP'].target)
            probe.apply('MajorYP',-1.,1.5);phases['press_closed']=run(1.5,'press_closed',-1.)
            probe.release();phases['press_released']=run(3.,'press_release')
            press={'creased_open_deg':press_before,'held_closed_deg':phases['press_closed']['MajorYP'],
                   'after_release_deg':phases['press_released']['MajorYP'],
                   'plastic_reference_after_deg':math.degrees(controller.states['HingeMajorYP'].target),
                   'spring_back_open_deg':phases['press_released']['MajorYP']-phases['press_closed']['MajorYP'],
                   'other_flaps_closed_during_press':max(peak('press_closed',f) for f in FLAPS if f!='MajorYP')}

            # Re-open that major flap before touching the minors: on an RSC the minors fold
            # under the majors, so a shut major traps them. That is the carton, not a bug.
            probe.apply('MajorYP',1.,.5);run(.5,'reopen_major',1.);probe.release();phases['major_reopened']=run(2.,'reopen_settle')

            # B: ramp the tip force from nothing and let go at 60 deg, short of the joint
            # limit, so the springback measured is the crease and not the limit stop.
            opening_force=None;force_at_target=None
            for step in range(1,51):
                force=step*.02;probe.apply('MajorYN',force)
                state=run(.1,'ramp',force)
                if opening_force is None and state['MajorYN']>5.:opening_force=force
                if state['MajorYN']>60.:force_at_target=force;break
            phases['ramp_end']=angles();probe.release();phases['ramp_released']=run(2.5,'ramp_release')

            # A: from the creased rest angle, a pull below yield must be a spring: it
            # deflects and comes back, and the permanent set must not move at all. Tried
            # from closed first, where a sub-yield pull cannot even lift the flap's own
            # weight, so that version measured nothing.
            before=controller.states['HingeMajorYN'].target;rest=angles()['MajorYN']
            sub_yield_force=round(.6*config['crease_gains']['MajorYN']['tip_force_to_start_creasing_n'],4)
            probe.apply('MajorYN',sub_yield_force,1.5);phases['sub_yield']=run(1.5,'sub_yield',sub_yield_force)
            probe.release();phases['sub_yield_released']=run(2.5,'sub_yield_release')
            sub_yield={'rest_deg':rest,'peak_deg':peak('sub_yield','MajorYN'),'returned_deg':phases['sub_yield_released']['MajorYN'],
                       'force_n':sub_yield_force,'plastic_reference_before_deg':math.degrees(before),
                       'plastic_reference_after_deg':math.degrees(controller.states['HingeMajorYN'].target)}

            # C: a minor flap, which on an RSC sits under the majors.
            probe.apply('MinorXP',.6,2.);phases['minor_pull']=run(2.,'minor_pull',.6)
            probe.release();phases['minor_released']=run(2.5,'minor_release')

            # E: the lever-arm prediction, bracketed. Grabbing halfway up the flap needs
            # twice the force of grabbing the outer edge, which is what a mouse drag near
            # the crease runs into.
            from parcel_forge.carton_feel import grab_force_table
            table=grab_force_table(config,'MinorXN');predicted=table['by_grab_point'][2]['force_n']
            probe.apply('MinorXN',round(predicted*.7,4),2.,fraction=.5);phases['half_grab_under']=run(2.,'half_grab_under',predicted*.7)
            probe.release();run(1.,'half_grab_gap')
            probe.apply('MinorXN',round(predicted*1.3,4),2.,fraction=.5);phases['half_grab_over']=run(2.,'half_grab_over',predicted*1.3)
            probe.release();phases['half_grab_released']=run(2.,'half_grab_release')

            # The picking force is an application setting; record that it can be read and
            # set from here, then put it back. What one unit is worth in newtons is not
            # documented in the installed package, so no claim is made about that.
            picking=controller.grab_strength();controller.grab_strength(20.);raised=controller.grab_strength()
            controller.grab_strength(picking['picking_force'] or 1.);restored=controller.grab_strength()

            # G: fold a flap right out, the way a person opens a box before reaching in.
            # 0 is shut, 90 straight up, 180 sticking out like a shelf, and 270 hanging
            # down the outside of the wall, which is what "opened right out" means.
            probe.apply('MajorYN',1.5,4.);phases['fold_back']=run(4.,'fold_back',1.5)
            probe.release();phases['fold_back_released']=run(3.,'fold_back_release')
            from pxr import Gf
            origin,quaternion=RigidPrim('/World/Carton/MajorYN').get_world_poses()
            hinge=[float(v) for v in origin.numpy()[0]];q=quaternion.numpy()[0]
            lever=config['width_m']/2-config['flap_tip_clearance_m']
            tip=[float(v) for v in Gf.Vec3d(*hinge)+Gf.Rotation(Gf.Quatd(float(q[0]),Gf.Vec3d(*map(float,q[1:])))).TransformDir(Gf.Vec3d(0,lever,0))]
            fold={'peak_deg':peak('fold_back','MajorYN'),'after_release_deg':phases['fold_back_released']['MajorYN'],
                  'wall_to_flap_angle_deg':phases['fold_back_released']['MajorYN']+90.,
                  'plastic_reference_deg':math.degrees(controller.states['HingeMajorYN'].target),
                  'limit_deg':config['crease_upper_limit_deg'],'hinge_m':hinge,'tip_m':tip,
                  'tip_below_hinge_m':hinge[2]-tip[2],'tip_outside_wall_m':abs(tip[1])-config['width_m']/2}

        # H: does the box itself move? A fixed base never should; a free one must slide
        # when pushed, and must not be dragged away by the force that opens a flap.
        box=RigidPrim('/World/Carton/Base')
        opening=config['crease_gains']['MajorYN']['tip_force_to_start_creasing_n']
        position=lambda:[float(v) for v in box.get_world_poses()[0].numpy()[0]]
        run(.5,'box_rest');rested=position()
        # Pull one flap first: opening a carton must not drag the carton across the table.
        flap_force=round(config['crease_gains']['MajorYP']['tip_force_to_start_creasing_n']*3.,4)
        probe.apply('MajorYP',flap_force,1.5);run(1.5,'box_flap_pull');probe.release();run(1.5,'box_flap_settle')
        after_flap=position()
        # Ramp a sideways force until the box breaks away, the same way the flap opening
        # force was measured. A single guessed shove told us nothing: 0.5 N did not move
        # it and 20 N threw it 33 m, so the threshold has to be measured.
        slide_force=None;slide_trace=[]
        for step in range(1,31):
            force=round(step*.1,3)
            for _ in range(round(.4/dt)):
                box.apply_forces_and_torques_at_pos(forces=[[force,0.,0.]],positions=[rested]);runtime.step();elapsed[0]+=dt
            moved=math.dist(position()[:2],after_flap[:2]);slide_trace.append({'force_n':force,'moved_m':moved})
            if moved>.002:slide_force=force;break
        run(1.5,'box_settle');after=position()
        body={'base_mode':config['base_mode'],'base_mass_kg':config['base_mass_kg'],
              'slide_force_n':slide_force,'slide_trace':slide_trace,
              'implied_friction_coefficient':(slide_force/(config['base_mass_kg']*9.81)) if slide_force else None,
              'moved_after_the_ramp_m':math.dist(after[:2],after_flap[:2]),
              'moved_by_opening_a_flap_m':math.dist(after_flap[:2],rested[:2]),
              'flap_pull_force_n':flap_force,'flap_opening_force_n':opening,
              'ground_friction':'PhysX default material; no material is authored yet, so this coefficient is the simulator default, not measured cardboard on a table'}

        span=lambda flap:(lambda values:max(values)-min(values))([row[FLAPS.index(flap)+3] for row in samples if row[0]>elapsed[0]-1.])
        springback=(peak('ramp','MajorYN')-phases['ramp_released']['MajorYN']) if flaps_tested else None
        checks={'panels_are_rigid':not config.get('panel_bend_joints'),
                'settled':max(span(f) for f in FLAPS)<.02*57.2957795,
                'no_drive_offset_commands':not controller.pulses,
                'callback_no_error':not controller.failed and not probe.failed,
                'box_responds_to_a_push_as_configured':(body['slide_force_n'] is not None) if config['base_mode']=='free' else (body['slide_force_n'] is None),
                'box_not_dragged_by_opening_a_flap':body['moved_by_opening_a_flap_m']<.02}
        if flaps_tested:
            checks.update({
         'sub_yield_pull_deflects_the_flap':sub_yield['peak_deg']-sub_yield['rest_deg']>.2,
         'sub_yield_pull_springs_back':abs(sub_yield['returned_deg']-sub_yield['rest_deg'])<.5,
         'sub_yield_pull_leaves_no_new_permanent_set':abs(sub_yield['plastic_reference_after_deg']-sub_yield['plastic_reference_before_deg'])<1e-9,
         'quick_pull_creases_the_flap':phases['quick_pull_released']['MajorYP']>10.,
         'quick_pull_leaves_the_neighbour_closed':peak('quick_pull','MinorXN')<5.,
         'opening_force_within_hand_range':opening_force is not None and .02<=opening_force<=1.,
         'released_short_of_the_joint_limit':peak('ramp','MajorYN')<config['crease_upper_limit_deg']-5.,
         'springback_matches_the_target':abs(springback-config['crease_targets']['springback_deg'])<3.,
         'major_stays_open_after_release':phases['ramp_released']['MajorYN']>10.,
         'minor_creases_and_stays':phases['minor_released']['MinorXP']>10.,
         # The untouched flap rests at its -5 deg stop, so abs() made this knife-edge.
         # What matters is that it did not open.
         'opposite_minor_undisturbed':phases['minor_released']['MinorXN']<5.,
         'half_grab_below_prediction_does_not_open':phases['half_grab_under']['MinorXN']<5.,
         'half_grab_above_prediction_opens':phases['half_grab_over']['MinorXN']>10.,
         'picking_force_readable_and_restorable':raised['picking_force']==20. and restored['picking_force']==(picking['picking_force'] or 1.),
         'folds_past_ninety_degrees':fold['peak_deg']>120.,
         'folds_back_to_the_wall':fold['peak_deg']>config['crease_upper_limit_deg']-15.,
         'stays_folded_back':fold['after_release_deg']>120.,
         'folded_flap_hangs_below_its_crease':fold['tip_below_hinge_m']>.05,
         'folded_flap_is_outside_the_wall':fold['tip_outside_wall_m']>-.001,
         'press_ran_with_the_other_flaps_shut':press['other_flaps_closed_during_press']<1.,
         'major_reopens_after_being_shut':phases['major_reopened']['MajorYP']>10.,
         'press_closed_stays_closed':abs(press['after_release_deg'])<8.,
         'press_closed_resets_the_crease':abs(press['plastic_reference_after_deg'])<8.,
         'press_spring_back_is_small':abs(press['spring_back_open_deg'])<8.,})
        with (out/'pull_trace.csv').open('w') as file:
            writer=csv.writer(file);writer.writerow(['time_s','phase','applied_tip_force_n']+[f+'_deg' for f in FLAPS]);writer.writerows(samples)
        extras=dict(press_closed=press,fold_back=fold,grab_force_table=table,half_grab_predicted_n=predicted,
                    opening_force_n=opening_force,tip_force_at_60_deg_n=force_at_target,sub_yield=sub_yield,
                    quick_pull_residual_deg=phases['quick_pull_released']['MajorYP'],ramp_peak_deg=peak('ramp','MajorYN'),
                    ramp_residual_deg=phases['ramp_released']['MajorYN'],springback_deg=springback,
                    half_grab_under_deg=phases['half_grab_under']['MinorXN'],half_grab_over_deg=phases['half_grab_over']['MinorXN'],
                    picking_force={'default_in_this_app':picking['picking_force'],'raised_to':raised['picking_force'],'restored_to':restored['picking_force'],
                                   'newtons_per_unit':'not documented in the installed omni.physx package; must be found by pulling'}) if flaps_tested else {}
        result.update(status='pass' if all(checks.values()) else 'fail',physics='pass',checks=checks,phases=phases,**extras,
                      body=body,samples=len(samples),
                      callback_run=str(controller.out),
                      scope='rigid panels with elasto-plastic creases under external tip forces; no open/close command, no calibrated cardboard, no native mouse or human view')
    except Exception as exc:result['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if controller:
            controller.close();result['cleanup']={'stage_released':controller.stage is None,'view_released':controller.view is None,'own_callbacks_removed':not controller.ids}
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');runtime.close()
    return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
