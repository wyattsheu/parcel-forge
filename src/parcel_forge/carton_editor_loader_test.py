"""Execute actual Script Editor entry in private Kit, including stale package path."""
import argparse,json,re,traceback
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);root=Path(__file__).resolve().parents[2];r=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);scope={};report={'status':'fail','native_mouse':'not_tested','human_webrtc':'not_tested','render':'not_tested'}
    try:
        r.start()
        import parcel_forge,omni.usd
        parcel_forge.__path__=['/tmp/parcel_forge_stale_lookup']
        loader=root/'scripts/carton_force_editor.py';exec(compile(loader.read_text(),str(loader),'exec'),scope)
        for _ in range(2000):
            r.app.update()
            if scope['_pf_live_task'].done():break
        scope['_pf_live_task'].result();controller=scope['pf_live'];r.stage=omni.usd.get_context().get_stage();r.configure_physics(gravity=9.81,enable_ccd=False);r.play();r.step(4);from isaacsim.core.experimental.prims import RigidPrim
        box=RigidPrim('/World/Carton/Base');before=[float(v) for v in box.get_world_poses()[0].numpy()[0]]
        # 0.30 N is the measured force that takes a major flap to 60 deg. The old 2 N
        # threw the whole free-standing box, which weighs 0.83 N, across the scene.
        controller.force_probe.apply('MajorYN',.3,2.);r.step(600)
        values=dict(zip(controller.names,map(float,controller.view.get_dof_positions().numpy()[0])))
        after=[float(v) for v in box.get_world_poses()[0].numpy()[0]]
        report['box_moved_m']=sum((a-b)**2 for a,b in zip(after[:2],before[:2]))**.5
        checks={'actual_loader_completed':scope['_pf_live_task'].done(),'stale_package_path_repaired':parcel_forge.__path__==[str(root/'src/parcel_forge')],'one_flap_physical_force':values['HingeMajorYN']>.5,'opposite_closed':abs(values['HingeMajorYP'])<.1,'box_not_shoved_by_one_flap':report['box_moved_m']<.01,'no_callback_error':not controller.failed and not controller.force_probe.failed}
        r._timeline.stop();r.app.update()
        # Execute the real loader again in same globals, exercising own cleanup/re-import.
        exec(compile(loader.read_text(),str(loader),'exec'),scope)
        for _ in range(2000):
            r.app.update()
            if scope['_pf_live_task'].done():break
        scope['_pf_live_task'].result();checks['second_load_completed']=scope['pf_live'] is not controller and controller.stage is None
        # Third load against a DIFFERENT asset: this is the swap the user performs, and
        # the one that can leave the previous stage resident while Kit closes it.
        text=loader.read_text();current=re.search(r"source='([^']+)'",text).group(1)
        others=sorted(q.parent.name for q in (root/'runs').glob('*ext1_carton_pull/asset.usda') if q.parent.name!=current)
        report['stage_swap']={'from':current,'to':others[-1] if others else None}
        if others:
            second=scope['pf_live']
            exec(compile(text.replace("source='%s'"%current,"source='%s'"%others[-1]),str(loader),'exec'),scope)
            for _ in range(2000):
                r.app.update()
                if scope['_pf_live_task'].done():break
            scope['_pf_live_task'].result()
            r.app.update();r.app.update()
            checks['stage_swap_completed']=scope['pf_live'] is not second and second.stage is None
            log=(out/'runtime.log')
            captured=log.read_text(errors='replace') if log.exists() else ''
            residents=[line for line in captured.splitlines() if 'Unexpected reference count' in line]
            report['resident_stage_warnings']=residents[:4]
            checks['no_resident_stage_on_swap']=not residents if captured else True
            report['log_captured']=bool(captured)
        report.update(status='pass' if all(checks.values()) else 'fail',checks=checks,angles_rad=values,scope='actual Python entry + async USD opening/UI construction/force in private headless Kit; not viewer mouse input')
    except Exception as exc:report['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if scope.get('pf_live'):scope['pf_live'].close()
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');r.close()
if __name__=='__main__':main()
