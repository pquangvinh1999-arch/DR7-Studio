"""Whole-pose identity revision; reference is exactly the Owner-selected power_up frame1."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from scipy import ndimage
from PIL import Image
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';RAW=S/'raw_frames';RAW.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
plan=read(W.parent/'atlas-v1/plan.json');plan.update(master=str((W/'canonical/master.png').relative_to(R)),master_sha256=sha(W/'canonical/master.png'),master_size_px=[160,70],owner_animation_approved=False)
master=Image.open(W/'canonical/master.png').convert('RGBA');old=read(W/'before-runtime/clips/animation-clips.json');oldbase=W/'before-runtime/clips'
frames=[];clips={};registered={};proof=[]
def cells(name,cols,rows,count):
 a=np.array(Image.open(W/f'generated/{name}.png').convert('RGBA'));a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
 labels,n=ndimage.label(a[:,:,3]>0,np.ones((3,3)));areas=np.bincount(labels.ravel());major=list(np.flatnonzero(areas[1:]>400)+1);assert len(major)==count,(name,len(major),count)
 seeds=np.isin(labels,major);nearest=ndimage.distance_transform_edt(~seeds,return_distances=False,return_indices=True);owner=labels[tuple(nearest)];ordered={}
 for lab in major:
  cy,cx=ndimage.center_of_mass(labels==lab);idx=int(cy//(a.shape[0]/rows))*cols+int(cx//(a.shape[1]/cols));assert idx not in ordered,(name,idx);ordered[idx]=lab
 out=[]
 for i in range(count):
  x0=round(i%cols*a.shape[1]/cols);y0=round(i//cols*a.shape[0]/rows);x1=round((i%cols+1)*a.shape[1]/cols);y1=round((i//cols+1)*a.shape[0]/rows)
  owned=a.copy();owned[(labels==0)|(owner!=ordered[i])]=0;pad=64
  tile=Image.fromarray(owned).crop((x0-pad,y0-pad,x1+pad,y1+pad));bb=tile.getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<tile.width and bb[3]<tile.height,(name,i,bb)
  out.append((tile,bb,[x0-pad,y0-pad,x1-x0+2*pad,y1-y0+2*pad]))
 return out
counts={'idle':12,'walk':12,'attack_light':16,'hit':6,'ko':8}
grids={'idle':(3,4),'walk':(3,4),'attack_light':(4,4),'hit':(3,2),'ko':(4,2)}
base_scale=None
for name,count in counts.items():
 cols,rows=grids[name];cc=cells(name,cols,rows,count);b0=cc[0][1]
 scale=(160/(b0[2]-b0[0])) if name!='walk' else base_scale
 if name=='idle':base_scale=scale
 rootx=b0[0]+78/scale;grounds={row:max(bb[3] for i,(_,bb,_) in enumerate(cc) if i//cols==row) for row in range(rows)};ims=[]
 for i,(tile,bb,rect) in enumerate(cc):
  ground=grounds[i//cols];out=tile.transform((384,256),Image.Transform.AFFINE,(1/scale,0,rootx-176/scale,0,1/scale,ground-224/scale),resample=Image.Resampling.NEAREST)
  canonical=(name=='idle' and i==0) or (name=='attack_light' and i in [0,15]) or (name=='hit' and i in [0,5]) or (name=='ko' and i==0)
  if canonical:out=master.copy()
  bounds=out.getbbox();assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<384 and bounds[3]<256,(name,i,bounds)
  ims.append(out);proof.append({'clip':name,'frame':i,'source':f'generated/{name}.png','source_sha256':sha(W/f'generated/{name}.png'),'source_component_cell':rect,'source_bbox':list(bb),'uniform_action_scale':scale,'root_x_source':rootx,'row_ground_source':ground,'canvas_bbox':list(bounds),'canonical_exact':canonical,'whole_pose_only':True})
 registered[name]=ims
# Preserve the selected ten power poses exactly; replace both former ready poses with the selected canonical.
# Merge identical old0/old1 ready hold into8ticks: release and total duration stay unchanged.
registered['power_up']=[Image.open(oldbase/old['frames'][old['clips']['power_up']['frames'][i]]['file']).convert('RGBA') for i in range(1,11)]+[master.copy()]
plan['ticks']['power_up']=[8,4,4,2,2,2,2,4,4,4,6];plan['body_actions']['power_up']=11
laser=plan['render_contract']['chilopoda']['laser'];laser['tip_anchors_by_frame']=laser['tip_anchors_by_frame'][1:11]+[laser['tip_anchors_by_frame'][1]];laser['release_frame']=3
registered['turn']=[registered['walk'][0]]+[registered['attack_light'][i] for i in [3,4,5,6,7,9,10,11,12]]+[registered['walk'][0]]
for n in plan['render_contract']['effect_clips']:
 registered[n]=[Image.open(oldbase/old['frames'][i]['file']).convert('RGBA') for i in old['clips'][n]['frames']]
for name,ims in registered.items():
 indices=[]
 for i,out in enumerate(ims):
  p=RAW/f'{name}_{i:02d}.png';out.save(p);indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name})
 prior=old['clips'][name];c={k:v for k,v in prior.items() if k in ['loop_policy','role','keys','events','hitstop_ticks']};c.update(frames=indices,ticks=plan['ticks'][name],loop_policy='cycle' if name in ['idle','walk'] else 'oneshot',role='fx' if name in plan['render_contract']['effect_clips'] else 'player')
 if name=='power_up':c.update(hitstop_ticks=0,keys={'wind_start':0,'wind_peak':2,'strike':3,'recover':7,'end':10},events=[{'at':3,'name':'custom:dual_laser_release'},{'at':10,'name':'end'}])
 clips[name]=c
for name,key in [('attack_light','burrow'),('turn','burrow_turn')]:
 c=plan['render_contract']['chilopoda'][key];c['top_y_by_frame']=[im.getbbox()[1] for im in registered[name]];c['frame_ticks']=plan['ticks'][name]
plan['identity_revision']={'source':'previous power_up frame1, exactPNG','owner_instruction':read(W/'canonical/approval.json')['owner_instruction'],'canonical_approval':str((W/'canonical/approval.json').relative_to(R)),'power_mapping':'new0..9=old1..10;new10=canonicalold1. Old0+old1 hold merged8ticks;42ticks total/release16 unchanged.','new_body_sources':list(counts),'turn_reuses':'New whole walk0 and whole attack poses, facing changes only when hidden','fx_pixels_unchanged':True}
write(W/'plan.json',plan);write(W/'registration.json',proof)
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':70,'anchor_px':[176,224],'shadow':{'rx':38,'ry':4,'opacity':.3},'frames':frames,'clips':clips,'states':old['states']}
write(S/'clips_manifest.json',manifest)
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for name,ims in registered.items():rv.review(name,ims,plan['ticks'][name])
print(json.dumps({'frames':len(frames),'clips':len(clips),'master_sha256':sha(W/'canonical/master.png'),'idle_scale':base_scale,'body_counts':{n:len(registered[n]) for n in plan['render_contract']['body_clips']}}))
