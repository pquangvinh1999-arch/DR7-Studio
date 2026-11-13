"""Resize source FX only; retain all complete body PNGs and authored body timelines."""
from pathlib import Path
import json,hashlib,shutil,sys,copy,importlib.util
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;R=W.parents[3];A=R/'assets/sarcosuchus';ST=W/'stage';V1=W.parent/'atlas-v1'
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def at(ticks,t):
 for i,d in enumerate(ticks):
  if t<d:return i
  t-=d
 return len(ticks)-1
if sys.argv[1]=='prepare':
 assert not (W/'baseline.json').exists(),'One-time snapshot; do not replace baseline'
 old=read(A/'clips/animation-clips.json');meta=read(A/'godot_bundle/engine-export.json');body=meta['render_contract']['body_clips'];out=[];clips={};proof={}
 for name in body:
  c=copy.deepcopy(old['clips'][name]);ids=[]
  for pos,idx in enumerate(c['frames']):
   src=A/'clips'/old['frames'][idx]['file'];dest=ST/'raw_frames'/f'{name}_{pos:02}.png';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);ids.append(len(out));out.append({'name':dest.stem,'file':str(dest.relative_to(ST))});proof[f'{name}:{pos}']={'sha256':sha(src),'ticks':c['ticks'][pos]}
  clips[name]={'frames':ids,'ticks':c['ticks'],'loop_policy':c['loop_policy'],'role':c['role']}
  for key in ['keys','events','hitstop_ticks']:
   if key in c:clips[name][key]=c[key]
  # Compiled events_ms is copied back into the input event schema.
  if 'events_ms' in c:clips[name]['events']=[{k:v for k,v in e.items() if k in ['at','name','data']} for e in c['events_ms']]
 protected={str(p.relative_to(R)):sha(p) for cid in ['t_rex','spinosaurus','pteranodon','tasmanian_king_crab'] for p in (R/'assets'/cid).rglob('*') if p.is_file() and not p.name.endswith('.import')}
 write(W/'baseline.json',{'body':proof,'meta':meta,'protected_peers':protected,'previous_atlas_sha256':sha(A/'godot_bundle/godot/sarcosuchus-atlas-00.png')})
 fx=[]
 for i in range(6):
  im=Image.open(V1/f'stage/raw_frames/energy_blast_{i:02}.png').convert('RGBA');s=33/10
  im=im.transform((384,256),Image.Transform.AFFINE,(s,0,176-176*s,0,s,128-128*s),resample=Image.Resampling.NEAREST);fx.append(im)
  p=ST/'raw_frames'/f'energy_blast_{i:02}.png';im.save(p);out.append({'name':p.stem,'file':str(p.relative_to(ST))})
 blastids=list(range(55,61));chargeids=[];growth=[];crop=fx[0].crop(fx[0].getbbox())
 for i,(width,opacity) in enumerate(zip([1,2,2,3,4,5,6,7,9,10],[32,64,96,128,160,192,224,255,255,255])):
  if i==9:im=fx[0].copy()
  else:
   tile=crop.resize((width,max(1,round(crop.height*width/crop.width))),Image.Resampling.NEAREST);a=np.array(tile);a[:,:,3]=np.rint(a[:,:,3].astype(float)*opacity/255).astype('uint8');tile=Image.fromarray(a);im=Image.new('RGBA',(384,256));im.alpha_composite(tile,(176-width//2,128-tile.height//2))
  p=ST/'raw_frames'/f'charge_{i:02}.png';im.save(p);chargeids.append(len(out));out.append({'name':p.stem,'file':str(p.relative_to(ST))});bb=im.getbbox();growth.append({'tick':i,'body_frame':i//5,'bbox_xyxy':bb,'size_px':[bb[2]-bb[0],bb[3]-bb[1]],'opacity_multiplier':opacity})
 clips['energy_blast_fx']={'frames':blastids,'ticks':[3]*6,'loop_policy':'oneshot','role':'fx'};clips['energy_charge_fx']={'frames':chargeids,'ticks':[1]*10,'loop_policy':'oneshot','role':'fx'}
 manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':34,'anchor_px':[176,224],'shadow':old['shadow'],'frames':out,'clips':clips,'states':old['states']}
 write(ST/'clips_manifest.json',manifest);write(W/'growth.json',growth)
 contract=copy.deepcopy(meta['render_contract']);contract['charge']['origin_canvas_px_by_frame']=[[236,201],[239,193]];contract['charge']['growth']='10 baked60Hz FX poses, fade32→255, width1→10px; jaw-matched';contract['projectile']['launch_size_matches_charge']=True;write(W/'contract.json',contract)
 print(json.dumps({'frames':len(out),'growth':growth,'launch_bbox':fx[0].getbbox()}))
elif sys.argv[1]=='review':
 m=read(ST/'clips/animation-clips.json');c=read(W/'contract.json');frames={name:[Image.open(ST/'clips'/m['frames'][i]['file']).convert('RGBA') for i in cl['frames']] for name,cl in m['clips'].items()};spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
 for name in ['energy_charge_fx','energy_blast_fx']:rv.review(name,frames[name],m['clips'][name]['ticks'])
 pics=[];samples=[];union=np.zeros((256,384),bool);toothproof=[]
 for name in c['body_clips']:
  for im in frames[name]:union|=np.array(im)[:,:,3]>0
 for t in range(46):
  bi=at(m['clips']['power_up']['ticks'],t);body=frames['power_up'][bi];im=body.copy();layer=Image.new('RGBA',(384,256))
  if t<10:fx=frames['energy_charge_fx'][t];point=c['charge']['origin_canvas_px_by_frame'][bi]
  elif t<28:fx=frames['energy_blast_fx'][(t-10)//3];point=[244+4*(t-10),194]
  else:fx=None
  if fx is not None:layer.alpha_composite(fx,(point[0]-176,point[1]-128));im.alpha_composite(layer)
  if t<=10:
   b=np.array(body);f=np.array(layer);teeth=(b[:,:,0]>=130)&(b[:,:,1]>=120)&(b[:,:,2]>=85)&(b[:,:,3]>0);region=np.zeros((256,384),bool);region[182:210,228:253]=True;yy,xx=np.where(teeth&region&(f[:,:,3]>0));toothproof.append({'tick':t,'overlap_bright_tooth_pixels':len(xx),'overlap_canvas_px':[[int(x),int(y)] for y,x in zip(yy,xx)]})
  pics.append(im);union|=np.array(im)[:,:,3]>0
  if t in list(range(11))+[13,16,19,22,25,27,28,45]:samples.append((t,im))
 rv.review('power_up-composite',[im for _,im in samples],[1]*len(samples));write(W/'review/sample-ticks.json',[t for t,_ in samples]);write(W/'verification/teeth-overlap.json',toothproof)
 for bg,color in [('light','#eee'),('dark','#171b24')]:
  ims=[]
  for im in pics:p=Image.new('RGBA',(384,256),color);p.alpha_composite(im);ims.append(p.resize((768,512),Image.Resampling.NEAREST))
  ims[0].save(W/f'review/playback-power_up-{bg}.webp',save_all=True,append_images=ims[1:],duration=[round((i+1)*1000/60)-round(i*1000/60) for i in range(46)],loop=0,lossless=True)
 y,x=np.where(union);write(W/'envelope.json',{'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)});print(json.dumps(toothproof))
elif sys.argv[1]=='install':
 base=read(W/'baseline.json');m=read(ST/'clips/animation-clips.json');meta=read(ST/'godot_bundle/engine-export.json');contract=read(W/'contract.json')
 for name in contract['body_clips']:
  for pos,idx in enumerate(m['clips'][name]['frames']):
   p=ST/'clips'/m['frames'][idx]['file'];assert sha(p)==base['body'][f'{name}:{pos}']['sha256'];assert m['clips'][name]['ticks'][pos]==base['body'][f'{name}:{pos}']['ticks']
  for field in ['ticks','events_ms','loop','keys','hitstop_ticks']:
   assert meta['clips'][name].get(field)==base['meta']['clips'][name].get(field),(name,field,meta['clips'][name].get(field),base['meta']['clips'][name].get(field))
 assert all(sha(R/p)==h for p,h in base['protected_peers'].items())
 meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']=base['meta']['provenance'];meta['provenance'].update(scaled_charge_variant_count=10,fx_revision='power-up-v2',fx_normalization='Existing keyed source whole FX resampled by10/33; source sphere max10x9; ten charge size/fade poses; launch PNG exactly equals last charge PNG.')
 write(ST/'godot_bundle/engine-export.json',meta)
 sidecars={str(p.relative_to(A)):p.read_bytes() for p in A.rglob('*.import')}
 for folder in ['clips','godot_bundle']:
  shutil.rmtree(A/folder);shutil.copytree(ST/folder,A/folder)
 for rel,data in sidecars.items():
  if (A/rel.removesuffix('.import')).exists():(A/rel).write_bytes(data)
 (A/'clips/.gdignore').touch();digest=sha(A/'godot_bundle/godot/sarcosuchus-atlas-00.png');roster=read(R/'assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='sarcosuchus');ch['render_contract']=contract
 motion=ch['motion_quality'];motion.update(atlas_sha256=digest,status='reviewed_pending_owner',review_evidence='work/characters/sarcosuchus/power-up-v2/review/keyframe-review.json',notes='Owner requested power_up FX revision: jaw-matched progressive1..10px sphere, finalcharge exactly matches launch PNG. All55bodyPNGs/timing/events frozen. Motion/naturalness pending Owner.')
 ch['qa_report']='docs/characters/sarcosuchus-power-up-v2-qa.json';mm=ch['map_sync_metrics'];box=read(W/'envelope.json');mm['full_fx_bbox_px']=box;mm['world_size_at_64ppu_m'].update(aura_w_m=round(box['w']/64,3),aura_h_m=round(box['h']/64,3));mm['tile_32px_span'].update(full_fx_tiles_w=round(box['w']/32,3),full_fx_tiles_h=round(box['h']/32,3));ch['pixel_sharpness_metrics']['reference_note']='Body1px unchanged; source FX nearest rescale10/33 of prior normalization, maximum charging orb10x9px; gradual10tick charge opacity/size. SoftFX permitted. No source redraw.';write(R/'assets/roster.json',roster)
 write(W/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,'filmstrips_opened':['power_up-composite','energy_charge_fx','energy_blast_fx'],'three_backgrounds':True,'body_frames_unchanged':55,'teeth_overlap_pixels':0,'launch_texture_equals_last_charge':True,'real_time':'pending browser','owner_approved':False})
 write(R/ch['qa_report'],{'character_id':'sarcosuchus','revision':'power-up-v2','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'body_frames_frozen':55,'frames':71,'clip_references':sum(len(c['frames']) for c in m['clips'].values()),'charge_frames':10,'source_fx_frames':6,'render_contract':contract,'growth':read(W/'growth.json'),'map_sync_metrics':mm,'motion_quality':motion,'technical_checks':'pending','teeth_evidence':'work/characters/sarcosuchus/power-up-v2/verification/teeth-overlap.json'})
 import datetime
 s=read(R/'state.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_at']=now;s['project']['version']='0.8.1';s['project']['version_history'].append({'version':'0.8.1','date':now,'summary':'Sarcosuchus power_up: progressive jaw-fit10x9px orb,10charge tick poses, identical size at launch; body/timing frozen. Owner review pending.'});s['current_focus'].update(status='power_up_v2_installed_pending_checks',summary='Sarco power_up v2:orb1→10px/fade, jaw-fitted, no measured tooth overlap before launch; lastcharge=firstprojectile exactRGBA.55bodyPNGs/ticks/events frozen,716peerfiles unchanged. Pending engine/browser/Owner checks.');write(R/'state.json',s);(R/'VERSION').write_text('0.8.1\n')
 for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
  p=R/f;p.write_text(p.read_text().replace('0.8.0','0.8.1'))
 print(json.dumps({'atlas_sha256':digest,'atlas':meta['atlas'],'body_unchanged':55,'peers':len(base['protected_peers'])}))
