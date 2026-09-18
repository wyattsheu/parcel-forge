"""Independent flap and external edge force test; no native mouse claim."""
import argparse,json,traceback
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime
from parcel_forge.panel_bending import author_segmented_carton

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);root=Path(__file__).resolve().parents[2]
    c=json.loads((root/'runs/20260917T121758Z_ext1_mdcd_bending/config.json').read_text());c.update(interaction_mode='external_forces_only',panel_constitutive_model='estimated_elastoplastic_strip_v1',panel_yield_curvature_per_m=2.,panel_plastic_time_s=.05,panel_segments=4,panel_stability_policy='record',panel_plastic_provenance='uncalibrated phenomenological damage proxy; yield curvature 2/m and relaxation time .05s assumed, not literature measurement')
    r=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);controller=None;report={'status':'fail','native_mouse_force':'not_tested','human_webrtc':'user_reported_previous_failure; new_version_not_tested','render':'not_tested'}
    try:
        r.start();author_segmented_carton(r.stage,c,c['material'])
        h=(c['width_m']/2-c.get('flap_tip_clearance_m',0))/4
        for x in c['panel_bend_joints'].values():x['yield_torque_nm']=x['stiffness_nm_rad']*h*c['panel_yield_curvature_per_m']
        r.configure_physics(gravity=9.81,enable_ccd=False);r.stage.GetRootLayer().Export(str(out/'asset.usda'));(out/'config.json').write_text(json.dumps(c,indent=2)+'\n')
        from parcel_forge.carton_live import LiveCarton
        controller=LiveCarton(c);controller.show_controls();first_probe=controller.force_probe;controller.show_controls();report["duplicate_ui_reuses_probe"]=controller.force_probe is first_probe;probe=controller.force_probe;r.play();r.step(4)
        def angles():return dict(zip(controller.names,map(float,controller.view.get_dof_positions().numpy()[0])))
        phases={};checks={}
        # Physical force on one closed outer edge: no target-position manipulation.
        probe.apply('MajorYN',2.,2.);r.step(480);phases['one_major_edge_force']=angles()
        checks['closed_major_opens_by_external_force']=phases['one_major_edge_force']['HingeMajorYN']>.5
        checks['opposite_major_not_commanded']=abs(phases['one_major_edge_force']['HingeMajorYP'])<.1
        probe.apply('MajorYN',1.);r.step(240);probe.apply('MajorYP',1.);r.step(720);phases['majors_opened_separately']=angles()
        probe.apply('MinorXP',1.,3);r.step(720);phases['one_minor_open']=angles()
        checks['one_minor_opens']=phases['one_minor_open']['HingeMinorXP']>.5
        checks['opposite_minor_not_commanded']=abs(phases['one_minor_open']['HingeMinorXN'])<.15
        probe.apply('MinorXN',1.,3);r.step(720);phases['second_minor_open']=angles();checks['second_minor_opens']=phases['second_minor_open']['HingeMinorXN']>.5
        probe.apply('MajorYN',35.,1.);r.step(240);phases['panel_loaded']=angles()
        plastic={n:s.target for n,s in controller.bend_states.items()};probe.release();r.step(960);phases['panel_released']=angles()
        own=[n for n in plastic if n.startswith('BendMajorYN')]
        checks['panel_plastic_reference_changes']=any(abs(plastic[n])>.01 for n in own)
        checks['panel_residual_bending']=any(abs(phases['panel_released'][n])>.005 for n in own)
        checks['callback_no_error']=not controller.failed and not probe.failed
        checks['duplicate_ui_reuses_probe']=report['duplicate_ui_reuses_probe']
        probe.release();probe.strike('MajorYN',-1.,.05);r.step(24);checks['strike_ends']=not probe.loads and not probe.failed
        checks['no_drive_offset_commands']=not controller.pulses
        try:controller.push('MajorYN',.08,1)
        except ValueError:checks['drive_offset_command_rejected']=True
        else:checks['drive_offset_command_rejected']=False
        report.update(status='pass' if all(checks.values()) else 'fail',checks=checks,phases=phases,panel_plastic_reference_rad=plastic,callback_run=str(controller.out),samples=controller.samples,scope='jointed strip interaction proxy, not calibrated cardboard or native mouse validation')
    except Exception as exc:report['status']='fail';report['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if controller:
            controller.close();report['cleanup']={'stage_released':controller.stage is None,'view_released':controller.view is None,'joints_released':not controller.joints,'own_callbacks_removed':not controller.ids}
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');r.close()
if __name__=='__main__':main()
