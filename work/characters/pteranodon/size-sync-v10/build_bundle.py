"""Apply the Owner-approved raster sizing transform to every complete pose and FX."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys,subprocess
from PIL import Image
import numpy as np
WORK=Path(__file__).resolve().parent;ROOT=WORK.parents[3];SRC=WORK/'source';STAGE=WORK/'stage';ASSET=ROOT/'assets/pteranodon'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if not (SRC/'animation-clips.json').exists():
 for name in ['animation-clips.json','source-manifest.json']:shutil.copyfile(ASSET/'clips'/name,SRC/name)
 for name in ['engine-export.json']:shutil.copyfile(ASSET/'godot_bundle'/name,SRC/name)
 shutil.copyfile(ASSET/'owner_approval.json',SRC/'owner_approval.json')
 shutil.copyfile(ASSET/'godot_bundle/godot/pteranodon-atlas-00.png',SRC/'previous-approved-atlas.png')
 m=json.loads((SRC/'animation-clips.json').read_text())
 for f in m['frames']:shutil.copyfile(ASSET/'clips'/f['file'],SRC/'frames'/Path(f['file']).name)
 protected={str(p.relative_to(ROOT)):sha(p) for cid in ['spinosaurus','t_rex'] for p in (ROOT/'assets'/cid).rglob('*') if p.is_file() and not p.name.endswith('.import')}
 write(WORK/'protected-peers.json',protected)
m=json.loads((SRC/'animation-clips.json').read_text());s=json.loads((SRC/'source-manifest.json').read_text());oldexport=json.loads((SRC/'engine-export.json').read_text())
# Inverse pixel map reproduces the approved size sample byte-for-byte. Same
# fixed map for ALL frames: no per-pose bbox normalization or part transforms.
A=193/158;B=131/107;C=79-97*A;D=73-96*B
matrix=(A,0,C,0,B,D)
def point(p):return [round((p[0]-C)/A),round((p[1]-D)/B)]
(STAGE/'raw_frames').mkdir(parents=True,exist_ok=True)
for f,entry in zip(m['frames'],s['frames']):
 im=Image.open(SRC/'frames'/Path(f['file']).name).convert('RGBA')
 out=im.transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
 assert out.getchannel('A').getbbox() and np.isin(np.array(out)[:,:,3],[0,255]).all()
 dest=STAGE/'raw_frames'/f"{f['name']}.png";out.save(dest);entry['file']='raw_frames/'+dest.name
sample=Image.open(ROOT/'work/reviews/character-size-v1/pteranodon-sample.png').convert('RGBA');idle=Image.open(STAGE/'raw_frames/idle_00.png').convert('RGBA')
assert idle.tobytes()==sample.tobytes(),'Must exactly reproduce Owner-approved sample'
s['body_height_px']=107;s['shadow']['rx']=round(s['shadow']['rx']/A);s['shadow']['ry']=round(s['shadow']['ry']/B)
write(STAGE/'clips_manifest.json',s)
contract=copy.deepcopy(oldexport['render_contract']);contract['fx_pivot_px']=point(contract['fx_pivot_px']);contract['projectile']['origin_canvas_px']=point(contract['projectile']['origin_canvas_px']);contract['projectile']['velocity_px_per_tick']=[round(contract['projectile']['velocity_px_per_tick'][0]/A,6),round(contract['projectile']['velocity_px_per_tick'][1]/B,6)]
write(WORK/'transform.json',{'canvas':[384,256],'anchor_px':s['anchor_px'],'inverse_affine':list(matrix),'forward_scale_xy':[1/A,1/B],'rounding_note':'Nominal158/193 uniform shrink; 131px reference height rounds to107px. The fixed raster map follows that approved sample exactly for every pose/FX. No per-frame fitting.','source_atlas_sha256':sha(SRC/'previous-approved-atlas.png'),'sample_rgba_exact':True,'render_contract':contract})
TOOLS=ROOT/'.agents/skills/generate2dsprite/scripts'
subprocess.run([sys.executable,str(TOOLS/'build_animation_clips.py'),'--manifest',str(STAGE/'clips_manifest.json'),'--output-dir',str(STAGE/'clips'),'--preview-background','all','--strict'],check=True)
subprocess.run([sys.executable,str(TOOLS/'export_engine.py'),'--clips',str(STAGE/'clips/animation-clips.json'),'--target','all','--output-dir',str(STAGE/'godot_bundle'),'--name','pteranodon','--sampling','nearest','--godot-fps','auto'],check=True)
new=json.loads((STAGE/'clips/animation-clips.json').read_text())
for name,c in new['clips'].items():
 for k in ['frames','ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
  assert c.get(k)==m['clips'][name].get(k),(name,k)
assert new['states']==m['states'];assert new['anchor_px']==m['anchor_px'];assert len(new['frames'])==61
meta=json.loads((STAGE/'godot_bundle/engine-export.json').read_text());meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']=copy.deepcopy(oldexport['provenance']);meta['provenance']['size_sync']={'transform':'work/characters/pteranodon/size-sync-v10/transform.json','source_atlas_sha256':sha(SRC/'previous-approved-atlas.png'),'sample_rgba_exact':True,'all61_frames_resampled':True,'timing_and_actions_unchanged':True,'owner_size_approved':True};write(STAGE/'godot_bundle/engine-export.json',meta)
# Compact full-pose filmstrips plus real-tick animated evidence.
spec=importlib.util.spec_from_file_location('review',ROOT/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=WORK
for name,c in new['clips'].items():rv.review(name,[Image.open(STAGE/'clips'/new['frames'][i]['file']).convert('RGBA') for i in c['frames']],c['ticks'])
ims=[];ticks=new['clips']['power_up']['ticks'];fxclip=new['clips']['sonic_screech_fx'];delta=tuple(a-b for a,b in zip(contract['projectile']['origin_canvas_px'],contract['fx_pivot_px']))
for pos,idx in enumerate(new['clips']['power_up']['frames']):
 im=Image.open(STAGE/'clips'/new['frames'][idx]['file']).convert('RGBA')
 elapsed=sum(ticks[2:pos]);ft=0
 if pos>=2 and elapsed<contract['projectile']['lifetime_ticks']:
  for i,t in zip(fxclip['frames'],fxclip['ticks']):
   ft+=t
   if elapsed<ft:im.alpha_composite(Image.open(STAGE/'clips'/new['frames'][i]['file']).convert('RGBA'),delta);break
 ims.append(im)
rv.review('power_up-composite',ims,ticks)
print(json.dumps({'stage':str(STAGE),'atlas_sha256':sha(STAGE/'godot_bundle/godot/pteranodon-atlas-00.png'),'sample_rgba_exact':True,'metadata_preserved':True,'render_contract':contract}))
