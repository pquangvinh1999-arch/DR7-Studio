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
 assert len(large)==count,(name,len(large));cols=6 if name=='power_up' else (3 if name=='hit' else 4);rowheight=1024/((count+cols-1)//cols);large.sort(key=lambda x:(int(x[2]//rowheight),x[1]));groups={i:[v[0]] for i,v in enumerate(large)}
 for lid,cx,cy,area in small:
  idx=min(range(count),key=lambda j:(cx-large[j][1])**2+(cy-large[j][2])**2);assert np.hypot(cx-large[idx][1],cy-large[idx][2])<220,(name,lid);groups[idx].append(lid)
 boxes=[];owned_images=[]
 for i in range(count):
  owned=np.isin(labels,groups[i]);ys,xs=np.where(owned);boxes.append([int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]);tile=a.copy();tile[~owned]=0;owned_images.append(Image.fromarray(tile))
 b0=boxes[0];scale=157/(b0[2]-b0[0]);root=b0[0]+(176-85)/157*(b0[2]-b0[0]);grounds={row:max(b[3] for i,b in enumerate(boxes) if i//cols==row) for row in range((count+cols-1)//cols)};indices=[]
 turn_roots=[root,boxes[1][0]+.5*(boxes[1][2]-boxes[1][0]),boxes[2][0]+.5*(boxes[2][2]-boxes[2][0]),boxes[3][0]+(1-(176-85)/157)*(boxes[3][2]-boxes[3][0])] if name=='turn' else None
 for i,im in enumerate(owned_images):
  source_root=turn_roots[i] if turn_roots else root+(i%cols)*(1536/cols);row=i//cols
  # Calibrated torso silhouette centroid (fixed hip ROI; unaffected by bright frills or leg shadow colour), not frill/head/tail bounds or presumed equally spaced cells.
  if name!='turn':
   owned=np.array(im);ymid0=int(grounds[row]-.60*(b0[3]-b0[1]));ymid1=int(grounds[row]-.32*(b0[3]-b0[1]));guess=root+(i%cols)*(1536/cols);x0=max(0,int(guess-.20*(b0[2]-b0[0])));x1=min(1536,int(guess+.20*(b0[2]-b0[0])));region=owned[max(0,ymid0):max(1,ymid1),x0:x1,3]>0;yy,xx=np.where(region)
   if len(xx):
    if i==0:root_centroid_offset=root-float(np.median(xx)+x0)
    source_root=float(np.median(xx)+x0)+root_centroid_offset
  matrix=(1/scale,0,source_root-176/scale,0,1/scale,grounds[row]-224/scale)
  out=im.transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
  canonical=(name=='idle' and i==0) or (name=='turn' and i==0) or (name=='power_up' and i in [0,23]) or (name=='attack_light' and i==0)
  if canonical:out=Image.open(R/'work/characters/dilophosaurus/master-review/frill-v2/master-gameplay-v2.png').convert('RGBA')
  b=out.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<384 and b[3]<256,(name,i,b)
  p=OUT/'raw_frames'/f'{name}_{i:02d}.png';out.save(p);indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name});evidence.append({'clip':name,'index':i,'source_sheet':str(src.relative_to(R)),'source_sha256':sha(src),'ownership_component_ids':groups[i],'source_bbox_xyxy':boxes[i],'shared_action_scale':scale,'shared_source_row_ground_y':grounds[row],'source_anatomical_root_x':source_root,'canvas_bbox_xyxy':b,'whole_canonical_pose':canonical,'body_part_transform':False,'sha256':sha(p)})
 clips[name]={'frames':indices,'ticks':plan['ticks'][name],'loop_policy':'cycle' if name in ['idle','walk'] else 'oneshot','role':'player'}
 if name=='attack_light':clips[name].update(keys={'wind_start':0,'wind_peak':2,'strike':4,'recover':6,'end':7},hitstop_ticks=3,events=[{'at':1,'name':'tell'},{'at':4,'name':'hit'},{'at':7,'name':'end'}])
 if name=='power_up':clips[name].update(keys={'wind_start':0,'wind_peak':2,'strike':3,'recover':18,'end':23},hitstop_ticks=0,events=[{'at':1,'name':'tell'}]+[{'at':i,'name':'custom:air_slash','data':{'target_slash':True}} for i in [3,8,13]]+[{'at':23,'name':'end'}])
 if name=='turn':clips[name]['events']=[{'at':0,'name':'in'},{'at':3,'name':'end'}]
 if name in ['hit','ko']:clips[name]['events']=[{'at':0,'name':'in'},{'at':count-1,'name':'hold' if name=='ko' else 'end'}]
# Owner crescent: key original single pose, then rotate whole FX and reveal/erase vertically.
src=W/'source/air-slash-owner.png';orig=np.array(Image.open(src).convert('RGBA'));key=orig[0,0,:3].astype(float);delta=np.max(abs(orig[:,:,:3].astype(float)-key),axis=2);fg=delta>16;a=orig.copy();a[:,:,3]=fg*255;a[~fg]=0;edge=fg&~ndimage.binary_erosion(fg);alpha=np.clip(np.max((orig[:,:,:3][edge].astype(float)-key)/(255-key),axis=1),1/255,1);rgb=(orig[:,:,:3][edge].astype(float)-(1-alpha[:,None])*key)/alpha[:,None];a[:,:,:3][edge]=np.clip(np.rint(rgb),0,255).astype('uint8');a[:,:,3][edge]=np.rint(alpha*255).astype('uint8')
keyed=Image.fromarray(a);bb=keyed.getbbox();tile=keyed.crop(bb).resize((26,48),Image.Resampling.NEAREST);base=Image.new('RGBA',(384,256));base.alpha_composite(tile,(176-13,128-24));base.save(W/'source/keyed-normalized-slash.png');fxproof=[]
for strike in plan['slash_schedule']:
 name=strike['clip'];whole=base.rotate(-strike['angle_deg'],resample=Image.Resampling.NEAREST,center=(176,128));box=whole.getbbox();ids=[];height=box[3]-box[1]
 for i in range(6):
  # Directed moving reveal front followed by a trailing erase front, never translating the effect centre.
  start=0 if i<3 else [1/3,2/3,7/8][i-3];end=[1/3,2/3,1][i] if i<3 else 1
  y0=box[1]+int(height*start);y1=box[1]+max(1,int(height*end))
  if strike['direction']=='bottom_to_top':y0,y1=box[3]-(y1-box[1]),box[3]-(y0-box[1])
  arr=np.array(whole);arr[:y0]=0;arr[y1:]=0;im=Image.fromarray(arr);assert im.getbbox(),(name,i,y0,y1)
  p=OUT/'raw_frames'/f'{name}_{i:02}.png';im.save(p);ids.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name});fxproof.append({'clip':name,'phase':i,'source_sha256':sha(src),'angle_deg':strike['angle_deg'],'direction':strike['direction'],'retained_canvas_rows_y0_y1':[y0,y1],'full_rotated_bbox_xyxy':box,'new_AI_art':False,'pivot_px':[176,128],'body_emission':False})
 clips[name]={'frames':ids,'ticks':[1]*6,'loop_policy':'oneshot','role':'fx'}
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':96,'anchor_px':[176,224],'shadow':{'rx':35,'ry':5,'opacity':.3},'frames':frames,'clips':clips,'states':{'idle':'idle','moving':'walk','attack':'attack_light','power':'power_up','hurt':'hit','dead':'ko','turn':'turn'}};write(OUT/'clips_manifest.json',manifest);write(W/'registration.json',evidence);write(W/'fx-source-evidence.json',{'source_sha256':sha(src),'source_size_px':[orig.shape[1],orig.shape[0]],'source_key_RGBA':orig[0,0].tolist(),'source_pose_count':1,'key_threshold':16,'keyed_crop_bbox_xyxy':bb,'whole_FX_size_before_rotation':[26,48],'edge_unmixed_px':int(edge.sum()),'timeline_transforms':fxproof})
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for name,c in clips.items():rv.review(name,[Image.open(OUT/frames[i]['file']).convert('RGBA') for i in c['frames']],c['ticks'])
print(json.dumps({'body_poses':sum(plan['body_actions'].values()),'source_FX':1,'baked_FX_phases':18,'PNGframes':len(frames),'clips':len(clips)}))
