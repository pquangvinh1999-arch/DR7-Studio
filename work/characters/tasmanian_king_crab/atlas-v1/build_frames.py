"""Register COMPLETE generated poses; preserve six keyed Owner FX poses, add two new bridges."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3];OUT=W/'stage';(OUT/'raw_frames').mkdir(parents=True,exist_ok=True)
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'plan.json').read_text());plan['proposed_ticks']['power_up']=[8,16,5,5,5,6,7,8]
records=[];frames=[];clips={};evidence=[]
for name,count in plan['body_actions'].items():
 src=W/'generated'/(('attack_nomal-v2' if name=='attack_nomal' else name)+'.png');a=np.array(Image.open(src).convert('RGBA'));assert a.shape==(1024,1536,4)
 mask=a[:,:,3]>=128;a[:,:,3]=mask*255;a[~mask,:3]=0
 # Component ownership includes disconnected dissolve pixels; no limb masks.
 labels,n=ndimage.label(mask);slices=ndimage.find_objects(labels)
 body=[];small=[]
 for i,sl in enumerate(slices,1):
  if sl is None:continue
  y,x=sl;pixel_count=int((labels[sl]==i).sum());cx=(x.start+x.stop)/2;cy=(y.start+y.stop)/2
  entry=(i,cx,cy,pixel_count)
  (body if pixel_count>1000 else small).append(entry)
 assert len(body)==count,(name,'expected complete bodies',len(body),count)
 body=sorted(body,key=lambda e:(int(e[2]//320),e[1]));groups={i:[e[0]] for i,e in enumerate(body)}
 for lid,cx,cy,pixels in small:
  k=min(range(count),key=lambda j:(cx-body[j][1])**2+(cy-body[j][2])**2)
  assert ((cx-body[k][1])**2+(cy-body[k][2])**2)**.5<210,(name,'unowned component',lid)
  groups[k].append(lid)
 boxes=[];tiles=[]
 for i in range(count):
  own=np.isin(labels,groups[i]);yy,xx=np.where(own);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));boxes.append(box)
  tile=a.copy();tile[~own]=0;tiles.append(Image.fromarray(tile))
 # Single scale per action, grounded shared line per sheet row. Never fit each pose.
 box0=boxes[0];scale=133/(box0[2]-box0[0]);rootx=(box0[0]+box0[2])/2
 ground={row:max(b[3] for i,b in enumerate(boxes) if i//4==row) for row in range((count+3)//4)}
 tick=plan['proposed_ticks'][name];indices=[]
 for i,(tile,box) in enumerate(zip(tiles,boxes)):
  col,row=i%4,i//4;source_rootx=rootx+col*384
  inv=(1/scale,0,source_rootx-176/scale,0,1/scale,ground[row]-224/scale)
  im=tile.transform((384,256),Image.Transform.AFFINE,inv,resample=Image.Resampling.NEAREST)
  if name=='idle' and i==0:im=Image.open(R/'work/characters/tasmanian_king_crab/size-master/master.png').convert('RGBA')
  b=im.getchannel('A').getbbox();assert b and min(b[:2])>0 and b[2]<384 and b[3]<256,(name,i,b)
  dest=OUT/'raw_frames'/f'{name}_{i:02d}.png';im.save(dest);indices.append(len(frames));frames.append({'name':f'{name}_{i:02d}','file':'raw_frames/'+dest.name})
  evidence.append({'clip':name,'index':i,'source_sheet':str(src.relative_to(R)),'source_sha256':sha(src),'ownership_component_ids':groups[i],'source_owned_bbox_xyxy':box,'source_row_ground_y':ground[row],'shared_action_scale':scale,'source_root_x':source_rootx,'body_part_transforms':False,'canvas_bbox_xyxy':b,'frame_sha256':sha(dest)})
 loop=name in ['idle','walk'];clips[name]={'frames':indices,'ticks':tick,'loop_policy':'cycle' if loop else 'oneshot','role':'player'}
 if name=='attack_nomal':clips[name].update(keys={'wind_start':0,'wind_peak':2,'strike':4,'recover':6,'end':7},events=[{'at':1,'name':'tell'},{'at':4,'name':'hit'},{'at':7,'name':'end'}],hitstop_ticks=2)
 if name=='power_up':clips[name].update(keys={'wind_start':0,'wind_peak':1,'strike':2,'recover':5,'end':7},events=[{'at':0,'name':'tell'},{'at':2,'name':'hit','data':{'projectile':'power_orb_projectile'}},{'at':7,'name':'end'}],hitstop_ticks=0)
 if name in ['hit','ko']:clips[name]['events']=[{'at':0,'name':'in'},{'at':count-1,'name':'hold' if name=='ko' else 'end'}]
# Owner sheet keying uses a full2D color mask, including enclosed pockets.
p=W/'source/power-orb-owner.png';orig=np.array(Image.open(p).convert('RGBA'));delta=np.max(np.abs(orig[:,:,:3].astype(int)-[0,0,128]),axis=2);fg=delta>16;labels,n=ndimage.label(fg);centers=np.array([44.5,143.5,248.5,350.5,448.5,551.5]);ownership=np.argmin(abs(np.arange(600)[:,None]-centers),axis=1)
fx=[];fx_evidence=[]
for i in range(6):
 slot=5-i;owned=fg&(ownership[None,:]==slot);yy,xx=np.where(owned);cx=round((xx.min()+xx.max())/2);cy=round((yy.min()+yy.max())/2)
 a=orig.copy();a[:,:,3]=owned*255;a[~owned]=0
 # Pocket-first key above, then unmix only a one-pixel boundary against known key.
 edge=owned & ~ndimage.binary_erosion(owned)
 unmix_edge=edge & (delta<48)
 alpha=np.clip(delta[unmix_edge]/48,1/255,1)
 rgb=(orig[:,:,:3][unmix_edge].astype(float)-(1-alpha[:,None])*np.array([0,0,128]))/alpha[:,None]
 a[:,:,:3][unmix_edge]=np.clip(np.rint(rgb),0,255).astype(np.uint8)
 a[:,:,3][unmix_edge]=np.rint(alpha*255).astype(np.uint8)
 tile=Image.fromarray(a);out=Image.new('RGBA',(384,256));out.alpha_composite(tile,(-cx+176,-cy+128));fx.append(out)
 fx_evidence.append({'index':i,'kind':'owner_source','sheet_sha256':sha(p),'source_center_px':[cx,cy],'source_owned_bbox_xyxy':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'source_interior_rgb_unchanged':True,'source_foreground_rgb_unchanged':False,'edge_unmix_only_px':int(unmix_edge.sum()),'opaque_key_px':0,'enclosed_key_pockets':0,'key_rgb':[0,0,128],'key_threshold_max_channel':16,'newly_generated':False})
newsrc=W/'generated/orb-bridges.png';new=Image.open(newsrc).convert('RGBA')
for i,(cx,cy) in enumerate([(438,528),(1096,526)],6):
 # Same whole-FX scale; low-alpha model halo is excluded before normalization.
 tile=new.crop((cx-146,cy-146,cx+146,cy+146));a=np.array(tile);a[a[:,:,3]<16]=0;tile=Image.fromarray(a).resize((75,75),Image.Resampling.NEAREST)
 out=Image.new('RGBA',(384,256));out.alpha_composite(tile,(176-37,128-37));fx.append(out);fx_evidence.append({'index':i,'kind':'imagegen_new_bridge','source_sha256':sha(newsrc),'source_crop_xywh':[cx-146,cy-146,292,292],'normalization':'wholeFX292->75nearest','newly_generated':True})
fx_indices=[]
for i,im in enumerate(fx):
 im=im.transform((384,256),Image.Transform.AFFINE,(2,0,-176,0,2,-128),resample=Image.Resampling.NEAREST)
 dest=OUT/'raw_frames'/f'power_orb_{i:02d}.png';im.save(dest);fx_indices.append(len(frames));frames.append({'name':f'power_orb_{i:02d}','file':'raw_frames/'+dest.name})
clips['power_orb_loop']={'frames':fx_indices,'ticks':[4]*8,'loop_policy':'cycle','role':'fx'}
clips['power_orb_projectile']={'frames':[fx_indices[i] for i in [5,6,7,0]],'ticks':[4]*4,'loop_policy':'oneshot','role':'fx'}
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':64,'anchor_px':[176,224],'shadow':{'rx':40,'ry':6,'opacity':0.3},'frames':frames,'clips':clips,'states':{'idle':'idle','moving':'walk','attack':'attack_nomal','power':'power_up','hurt':'hit','dead':'ko'}}
write(OUT/'clips_manifest.json',manifest);write(W/'registration.json',evidence);write(W/'fx-source-evidence.json',fx_evidence)
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for name,c in clips.items():rv.review(name,[Image.open(OUT/frames[i]['file']).convert('RGBA') for i in c['frames']],c['ticks'])
print(json.dumps({'frames':len(frames),'clips':len(clips),'body_frames':46,'fx_frames':8,'source_fx':6,'new_fx':2}))
