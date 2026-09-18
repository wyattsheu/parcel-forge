"""Real headless callback test; no claim about WebRTC/native mouse input."""
import argparse,json,traceback
from pathlib import Path
from parcel_forge.runtime.isaacsim_runtime import IsaacSimRuntime

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);root=Path(__file__).resolve().parents[2]
    source=root/'runs/20260917T114330Z_ext1_carton';config=json.loads((source/'config.json').read_text());r=IsaacSimRuntime(dt=1/240,device='cpu',enable_cameras=False);controller=None;report={'status':'fail','human_mouse_input':'not_tested','ui_panel':'not_tested','render':'not_tested'}
    try:
        r.start()
        from pxr import Usd
        loaded=Usd.Stage.Open(str(source/'asset.usda'));r.stage.GetRootLayer().TransferContent(loaded.GetRootLayer());r.configure_physics(gravity=9.81,enable_ccd=False)
        from parcel_forge.carton_live import attach
        controller=attach(show_ui=False);controller.show_controls();report['ui_panel']='construction_executed_headless; human_view_not_tested';r.play();r.step(4)
        controller.push('MajorYN',.08,3);controller.push('MajorYP',.08,3);r.step(1200)
        states={n:{'plastic_target_rad':s.target,'accumulated_plastic_rad':s.accumulated_plastic} for n,s in controller.states.items()}
        checks={'callback_executed':controller.samples>1000,'callback_no_error':not controller.failed,'two_major_plastic':all(states['Hinge'+n]['plastic_target_rad']>.01 for n in ['MajorYN','MajorYP'])}
        report.update(status='pass' if all(checks.values()) else 'fail',checks=checks,states=states,callback_run=str(controller.out),samples=controller.samples)
    except Exception as exc:report['error']=str(exc);(out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        if controller:controller.close()
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');r.close()
if __name__=='__main__':main()
