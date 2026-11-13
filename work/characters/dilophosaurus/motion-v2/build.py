"""Whole-body generated motion revision; never cut or patch head/limbs/frills."""
from pathlib import Path
import json,hashlib,shutil,importlib.util
from PIL import Image
import numpy as np
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3];A=R/'assets/dilophosaurus';ST=W/'stage';base=json.load(open(W/'baseline.json'));old=base['manifest'];frames=[];clips={};registration=[]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def add(im,name):
 p=ST/'raw_frames'/f'{name}.png';im.save(p);frames.append({'name':name,'file':'raw_frames/'+p.name});return len(frames)-1
# Copy original full frames for every action except idle and power_up, including turn and all target FX.
for n,c in old['clips'].items():
 if n in ['idle','power_up']:continue
 ids=[]
 for pos,idx in enumerate(c['frames']):
  src=A/'clips'/old['frames'][idx]['file'];p=ST/'raw_frames'/f'{n}_{pos:02}.png';shutil.copyfile(src,p);ids.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name});assert sha(p)==base['frame_sha256_by_clip'][n][pos]
 clips[n]={'frames':ids,'ticks':c['ticks'],'loop_policy':c['loop_policy'],'role':c['role']}
 for field in ['keys','hitstop_ticks']:
  if field in c:clips[n][field]=c[field]
 clips[n]['events']=[{k:v for k,v in e.items() if k in ['name','at','data']} for e in c.get('events_ms',[])]
def extract(name,count,cols,target_width=157,target_height=None):
 p=W/'generated'/f'{name}.png';a=np.array(Image.open(p).convert('RGBA'));mask=a[:,:,3]>=128;a[:,:,3]=mask*255;a[~mask]=0;lab,_=ndimage.label(mask);groups=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  yy,xx=sl;area=int((lab[sl]==i).sum())
  if area>1000:groups.append([i,(xx.start+xx.stop)/2,(yy.start+yy.stop)/2])
 rowheight=1024/((count+cols-1)//cols);groups.sort(key=lambda e:(int(e[2]//rowheight),e[1]));assert len(groups)==count,(name,len(groups));owned=[];boxes=[]
 for i,g in enumerate(groups):
  m=lab==g[0];ys,xs=np.where(m);bb=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];boxes.append(bb);ar=a.copy();ar[~m]=0;owned.append(Image.fromarray(ar))
 # Keep any small detached detail with its nearest whole pose; no organ reconstruction.
 for lid,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None or any(lid==g[0] for g in groups):continue
  yy,xx=sl;cx=(xx.start+xx.stop)/2;cy=(yy.start+yy.stop)/2;i=min(range(count),key=lambda j:(cx-groups[j][1])**2+(cy-groups[j][2])**2);ar=np.array(owned[i]);ar[lab==lid]=a[lab==lid];owned[i]=Image.fromarray(ar)
 b0=boxes[0];scale=target_height/(b0[3]-b0[1]) if target_height else target_width/(b0[2]-b0[0]);root=b0[0]+(176-85)/157*(b0[2]-b0[0]);ground={row:max(b[3] for i,b in enumerate(boxes) if i//cols==row) for row in range((count+cols-1)//cols)};result=[]
 for i,im in enumerate(owned):
  row=i//cols;guess=root+(i%cols)*1536/cols;y0=int(ground[row]-.60*(b0[3]-b0[1]));y1=int(ground[row]-.32*(b0[3]-b0[1]));x0=max(0,int(guess-.2*(b0[2]-b0[0])));x1=min(1536,int(guess+.2*(b0[2]-b0[0])));arr=np.array(im);yy,xx=np.where(arr[y0:y1,x0:x1,3]>0)
  if len(xx):
   if i==0:offset=root-float(np.median(xx)+x0)
   source_root=float(np.median(xx)+x0)+offset
  else:source_root=guess
  out=im.transform((384,256),Image.Transform.AFFINE,(1/scale,0,source_root-176/scale,0,1/scale,ground[row]-224/scale),resample=Image.Resampling.NEAREST);result.append(out);registration.append({'clip':name,'phase':i,'source_bbox_xyxy':boxes[i],'scale':scale,'source_root_x':source_root,'ground':ground[row],'bbox_xyxy':out.getbbox(),'whole_pose_only':True,'source_sha256':sha(p)})
 return result
idle=extract('idle',12,4,target_height=96)
# Retain approved ready pose, compare other whole poses at native scale before publishing.
idle[0]=Image.open(R/'work/characters/dilophosaurus/master-review/frill-v2/master-gameplay-v2.png').convert('RGBA')
clips['idle']={'frames':[add(im,f'idle_{i:02}') for i,im in enumerate(idle)],'ticks':[10]*12,'loop_policy':'cycle','role':'player'}
wave=extract('power_wave',8,4,target_width=166);waveids=[add(im,f'power_wave_{i:02}') for i,im in enumerate(wave)]
def old_power(pos):return Image.open(A/'clips'/old['frames'][old['clips']['power_up']['frames'][pos]]['file']).convert('RGBA')
prep=[add(old_power(i),f'power_prepare_{i}') for i in [0,1]];recovery=[add(old_power(i),f'power_recover_{i}') for i in range(18,24)]
clips['power_up']={'frames':prep+[waveids[i%8] for i in range(30)]+recovery,'ticks':[4,4]+[2]*30+[3,3,3,3,3,5],'loop_policy':'oneshot','role':'player','hitstop_ticks':0,'keys':{'wind_start':0,'wind_peak':2,'strike':4,'recover':32,'end':37},'events':[{'at':1,'name':'tell'},{'at':37,'name':'end'}]}
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':96,'anchor_px':[176,224],'shadow':old['shadow'],'frames':frames,'clips':clips,'states':old['states']};write(ST/'clips_manifest.json',manifest);write(W/'registration.json',registration)
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
rv.review('idle',idle,[10]*12);rv.review('power_wave',wave,[2]*8);rv.review('power_up',[old_power(0),old_power(1)]+[wave[i%8] for i in range(30)]+[old_power(i) for i in range(18,24)],clips['power_up']['ticks'])
print(json.dumps({'raw_frames':len(frames),'clip_refs':sum(len(c['frames']) for c in clips.values()),'idle_bbox':[im.getbbox() for im in idle],'wave_bbox':[im.getbbox() for im in wave]}))
