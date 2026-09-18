"""Runs only in the isolated TripoSR Python. Model inference, no Isaac imports."""
import argparse, json, time, hashlib, sys, traceback
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--model',required=True);p.add_argument('--component-policy',choices=['keep','largest'],default='keep');a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'external/TripoSR'))
 result={'status':'fail','generation':'not_tested','physics':'not_tested','render':'not_requested','human_webrtc':'not_tested'};t=time.monotonic()
 try:
  import torch, numpy as np, rembg
  from PIL import Image
  from tsr.system import TSR
  from tsr.utils import remove_background,resize_foreground
  torch.set_num_threads(4);torch.manual_seed(0)
  if not torch.cuda.is_available():raise RuntimeError('qualified CUDA backend unavailable')
  torch.cuda.reset_peak_memory_stats()
  original=Image.open(a.input).convert('RGB');original.save(out/'input_original.png')
  session=rembg.new_session('u2netp',providers=['CPUExecutionProvider']);cut=resize_foreground(remove_background(original,session),.85);cut.save(out/'input_foreground.png');arr=np.array(cut).astype(np.float32)/255.;rgb=arr[:,:,:3]*arr[:,:,3:4]+(1-arr[:,:,3:4])*.5;image=Image.fromarray((rgb*255).astype(np.uint8));image.save(out/'input_model.png')
  pt=time.monotonic();model=TSR.from_pretrained(a.model,config_name='config.yaml',weight_name='model.ckpt');model.renderer.set_chunk_size(8192);model.to('cuda');torch.cuda.synchronize();loaded=time.monotonic()
  with torch.no_grad():codes=model([image],device='cuda');torch.cuda.synchronize();inferred=time.monotonic();mesh=model.extract_mesh(codes,has_vertex_color=True,resolution=128)[0]
  torch.cuda.synchronize();extracted=time.monotonic()
  from parcel_forge.image_mesh_cleanup import face_components
  groups=face_components(mesh.faces,len(mesh.vertices));mesh.export(out/'mesh_raw.obj')
  cleanup={'policy':a.component_policy,'raw_component_face_counts':[len(g) for g in groups],'removed_face_count':0,'human_removed_part_review':'not_tested'}
  if a.component_policy=='largest' and len(groups)>1:
   import trimesh
   def subset(indices):
    f=np.asarray(mesh.faces)[indices];used=np.unique(f);lookup=np.full(len(mesh.vertices),-1,dtype=np.int64);lookup[used]=np.arange(len(used));return trimesh.Trimesh(vertices=mesh.vertices[used],faces=lookup[f],vertex_colors=mesh.visual.vertex_colors[used],process=False)
   removed=[i for g in groups[1:] for i in g];subset(removed).export(out/'removed_components.obj');cleanup['removed_face_count']=len(removed);mesh=subset(groups[0])
  (out/'mesh_cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n');mesh.export(out/'mesh.obj');mesh.export(out/'mesh.glb')
  result.update(status='pass',generation='pass',input_sha256=digest(Path(a.input)),seed=0,mc_resolution=128,provider='TripoSR',model_directory=a.model,preprocessing='u2netp CPU background removal, foreground ratio .85, grey composite',component_cleanup=cleanup,source_size=list(original.size),vertex_count=len(mesh.vertices),face_count=len(mesh.faces),model_load_seconds=loaded-pt,inference_seconds=inferred-loaded,mesh_extract_seconds=extracted-inferred,peak_allocated_vram_bytes=torch.cuda.max_memory_allocated(),torch_version=torch.__version__,device=torch.cuda.get_device_name(0),obj_sha256=digest(out/'mesh.obj'),shape_fidelity='not_tested',metric_scale='assumed_after_conversion')
 except Exception as e:result['error']=repr(e);traceback.print_exc()
 finally:
  result['total_seconds']=time.monotonic()-t;(out/'provider_result.json').write_text(json.dumps(result,indent=2)+'\n')
 return 0 if result['status']=='pass' else 1

if __name__=='__main__':raise SystemExit(main())
