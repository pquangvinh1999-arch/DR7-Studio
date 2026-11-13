"""Whole-pose registration + source-preserving2Dmask FX extraction; no limb rigging."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from PIL import Image
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3];OUT=W/'stage';(OUT/'raw_frames').mkdir(parents=True,exist_ok=True)
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();plan=json.load(open(W/'plan.json'));frames=[];clips={};evidence=[]
for name,count in plan['body_actions'].items():
 src=W/'generated'/f'{name}.png';a=np.array(Image.open(src).convert('RGBA'));assert a.shape==(1024,1536,4);mask=a[:,:,3]>=128;a[:,:,3]=mask*255;a[~mask,:3]=0;labels,n=ndimage.label(mask);large=[];small=[]
 for i,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  y,x=sl;area=int((labels[sl]==i).sum());entry=(i,(x.start+x.stop)/2,(y.start+y.stop)/2,area)
  (large if area>1000 else small).append(entry)
 assert len(large)==count,(name,len(large));large.sort(key=lambda x:(int(x[2]//320),x[1]));groups={i:[v[0]] for i,v in enumerate(large)}
 for lid,cx,cy,area in small:
  idx=min(range(count),key=lambda j:(cx-large[j][1])**2+(cy-large[j][2])**2);assert np.hypot(cx-large[idx][1],cy-large[idx][2])<220,(name,lid);groups[idx].append(lid)
 boxes=[];owned_images=[]
 for i in range(count):
  owned=np.isin(labels,groups[i]);ys,xs=np.where(owned);boxes.append([int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]);tile=a.copy();tile[~owned]=0;owned_images.append(Image.fromarray(tile))
 b0=boxes[0];scale=157/(b0[2]-b0[0]);root=b0[0]+(176-89)/157*(b0[2]-b0[0]);grounds={row:max(b[3] for i,b in enumerate(boxes) if i//4==row) for row in range((count+3)//4)};indices=[]
 turn_roots=[root,600,960,boxes[3][0]+(1-(176-89)/157)*(boxes[3][2]-boxes[3][0])] if name=='turn' else None
 for i,im in enumerate(owned_images):
  source_root=turn_roots[i] if turn_roots else root+(i%4)*384;row=i//4;matrix=(1/scale,0,source_root-176/scale,0,1/scale,grounds[row]-224/scale)
  out=im.transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
  canonical=(name=='idle' and i==0) or (name=='turn' and i==0)
  if canonical:out=Image.open(R/'work/characters/sarcosuchus/master-review/master-gameplay-v1.png').convert('RGBA')
  b=out.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<384 and b[3]<256,(name,i,b)
  p=OUT/'raw_frames'/f'{name}_{i:02d}.png';out.save(p);indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name});evidence.append({'clip':name,'index':i,'source_sheet':str(src.relative_to(R)),'source_sha256':sha(src),'ownership_component_ids':groups[i],'source_bbox_xyxy':boxes[i],'shared_action_scale':scale,'shared_source_row_ground_y':grounds[row],'source_anatomical_root_x':source_root,'canvas_bbox_xyxy':b,'whole_canonical_pose':canonical,'body_part_transform':False,'sha256':sha(p)})
 clips[name]={'frames':indices,'ticks':plan['ticks'][name],'loop_policy':'cycle' if name in ['idle','walk'] else 'oneshot','role':'player'}
 if name=='attack_nomal':clips[name].update(keys={'wind_start':0,'wind_peak':2,'strike':4,'recover':6,'end':7},hitstop_ticks=3,events=[{'at':1,'name':'tell'},{'at':4,'name':'hit'},{'at':7,'name':'end'}])
 if name=='power_up':clips[name].update(keys={'wind_start':0,'wind_peak':1,'strike':2,'recover':6,'end':8},hitstop_ticks=0,events=[{'at':0,'name':'tell'},{'at':2,'name':'hit','data':{'projectile':'energy_blast_fx'}},{'at':8,'name':'end'}])
 if name=='turn':clips[name]['events']=[{'at':0,'name':'in'},{'at':3,'name':'end'}]
 if name in ['hit','ko']:clips[name]['events']=[{'at':0,'name':'in'},{'at':count-1,'name':'hold' if name=='ko' else 'end'}]
# Six source poses only, no redraw/extra energy poses. Island ownership is2D.
src=W/'source/power-up-owner.png';orig=np.array(Image.open(src).convert('RGBA'));key=np.array([0,128,0]);delta=np.max(abs(orig[:,:,:3].astype(int)-key),axis=2);fg=delta>16;centers=[[40,90],[155,96],[270,96],[362,88],[497,82],[620,81]];component_labels,_=ndimage.label(ndimage.binary_dilation(fg,structure=np.ones((5,5)),iterations=1));ownership=np.full(fg.shape,-1,dtype=int);source_component_ids=[[] for _ in range(6)]
for label,sl in enumerate(ndimage.find_objects(component_labels),1):
 if sl is None:continue
 component=(component_labels==label)&fg;yy,xx=np.where(component)
 if not len(xx):continue
 slot=int(np.searchsorted([80,191,313,422,558],float(xx.mean())))
 ownership[component]=slot;source_component_ids[slot].append(label)
fx=[];fproof=[]
for i,(cx,cy) in enumerate(centers):
 mask=ownership==i;ys,xs=np.where(mask);a=orig.copy();a[:,:,3]=mask*255;a[~mask]=0
 # Solve green-key contamination using blue/white source FX: foreground G <= max(R,B).
 rgb0=orig[:,:,:3].astype(float);excess=rgb0[:,:,1]-np.maximum(rgb0[:,:,0],rgb0[:,:,2]);mixed=mask&(excess>0)
 alpha=np.clip(1-excess[mixed]/128,1/255,1);rgb=(rgb0[mixed]-(1-alpha[:,None])*key)/alpha[:,None];a[:,:,:3][mixed]=np.clip(np.rint(rgb),0,255).astype(np.uint8);a[:,:,3][mixed]=np.rint(alpha*255).astype(np.uint8)
 raw=Image.new('RGBA',(384,256));raw.alpha_composite(Image.fromarray(a),(-cx+176,-cy+128));out=raw.transform((384,256),Image.Transform.AFFINE,(2,0,-176,0,2,-128),resample=Image.Resampling.NEAREST);fx.append(out)
 fproof.append({'index':i,'source_sha256':sha(src),'source_center_px':[cx,cy],'ownership_2d_component_ids':source_component_ids[i],'source_bbox_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'source_pose':True,'new_AI_pose':False,'uncontaminated_source_RGB_preserved':True,'pocket_first_key':[0,128,0],'threshold_max_channel':16,'green_contamination_unmixed_px':int(mixed.sum()),'whole_FX_scale':.5})
fx_indices=[]
for i,im in enumerate(fx):
 p=OUT/'raw_frames'/f'energy_blast_{i:02d}.png';im.save(p);fx_indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name})
p=OUT/'raw_frames/charge_small.png';fx[0].transform((384,256),Image.Transform.AFFINE,(2,0,-176,0,2,-128),resample=Image.Resampling.NEAREST).save(p);smallidx=len(frames);frames.append({'name':'charge_small','file':'raw_frames/'+p.name})
clips['energy_blast_fx']={'frames':fx_indices,'ticks':[3]*6,'loop_policy':'oneshot','role':'fx'};clips['energy_charge_fx']={'frames':[smallidx,fx_indices[0]],'ticks':[5,5],'loop_policy':'oneshot','role':'fx'}
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':34,'anchor_px':[176,224],'shadow':{'rx':43,'ry':5,'opacity':.3},'frames':frames,'clips':clips,'states':{'idle':'idle','moving':'walk','attack':'attack_nomal','power':'power_up','hurt':'hit','dead':'ko','turn':'turn'}};write(OUT/'clips_manifest.json',manifest);write(W/'registration.json',evidence);write(W/'fx-source-evidence.json',fproof)
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for name,c in clips.items():rv.review(name,[Image.open(OUT/frames[i]['file']).convert('RGBA') for i in c['frames']],c['ticks'])
print(json.dumps({'body_poses':55,'source_FX':6,'scaled_charge_variant':1,'PNGframes':len(frames),'clips':len(clips),'refs':sum(len(c['frames']) for c in clips.values())}))
