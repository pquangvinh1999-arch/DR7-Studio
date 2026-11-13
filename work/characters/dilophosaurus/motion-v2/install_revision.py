"""Install reviewed whole-pose revision while protecting all other actions and peers."""
from pathlib import Path
import json, hashlib, shutil, datetime, importlib.util, sys
from PIL import Image, ImageDraw
import numpy as np
W=Path(__file__).resolve().parent; R=W.parents[3]; ST=W/'stage'; A=R/'assets/dilophosaurus'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
base=read(W/'baseline.json'); m=read(ST/'clips/animation-clips.json'); meta=read(ST/'godot_bundle/engine-export.json')
review=read(W/'review/keyframe-review.json')
assert review['status']=='reviewed_pending_owner', 'Visual review must precede publication'
assert all(review['checks'].values()), 'Unresolved motion/identity problems block installation'
protected=read(W/'protected-peers.json')
assert all(sha(R/p)==h for p,h in protected.items())
frozen=[]
for name,c in base['manifest']['clips'].items():
 if name in ['idle','power_up']:continue
 n=m['clips'][name]
 for field in ['ticks','loop_policy','role','events_ms']:
  assert n.get(field)==c.get(field),(name,field)
 hashes=[sha(ST/'clips'/m['frames'][i]['file']) for i in n['frames']]
 assert hashes==base['frame_sha256_by_clip'][name],name
 frozen.append(name)
meta['source']['path']='../clips/animation-clips.json'
meta['render_contract']=base['meta']['render_contract']
meta['provenance']=dict(base['meta']['provenance'],revision='motion-v2',motion_revision_scope=['idle','power_up'],turn_retained=True,body_part_cut_warp=False)
write(ST/'godot_bundle/engine-export.json',meta)
digest=sha(ST/'godot_bundle/godot/dilophosaurus-atlas-00.png'); review['atlas_sha256']=digest
ims={n:[Image.open(ST/'clips'/m['frames'][i]['file']).convert('RGBA') for i in c['frames']] for n,c in m['clips'].items()}
union=np.zeros((256,384),bool)
for n in meta['render_contract']['body_clips']:
 for im in ims[n]:union|=np.array(im)[:,:,3]>0
def at(ticks,t):
 for i,d in enumerate(ticks):
  if t<d:return i
  t-=d
 return len(ticks)-1
composite=[];trace=[]
for t in range(88):
 bi=at(m['clips']['power_up']['ticks'],t); im=ims['power_up'][bi].copy()
 strike=next((s for s in meta['render_contract']['target_slashes']['strikes'] if s['at_tick']<=t<s['at_tick']+6),None)
 point=meta['render_contract']['target_slashes']['default_target_canvas_px']
 if strike:im.alpha_composite(ims[strike['clip']][t-strike['at_tick']],(point[0]-176,point[1]-128))
 union|=np.array(im)[:,:,3]>0;composite.append(im)
 trace.append({'tick':t,'body_frame':bi,'slash':strike['clip'] if strike else None,'phase':t-strike['at_tick'] if strike else None,'point':point if strike else None})
write(W/'verification/88tick-trace.json',trace)
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
sample=[0,4,8,12,14,17,23,31,33,36,46,50,52,55,65,68,77,87]
rv.review('power_up-composite',[composite[t] for t in sample],[1]*len(sample))
for bg in ['light','dark','checker']:
 pics=[]
 for im in composite:
  back=Image.new('RGBA',(384,256),'#eee8dc' if bg=='light' else '#171b23')
  if bg=='checker':
   d=ImageDraw.Draw(back)
   for y in range(0,256,8):
    for x in range(0,384,8):d.rectangle((x,y,x+7,y+7),fill='#bbb' if (x//8+y//8)%2 else '#ddd')
  back.alpha_composite(im);pics.append(back.resize((768,512),Image.Resampling.NEAREST))
 pics[0].save(W/f'review/playback-power_up-composite-{bg}.webp',save_all=True,append_images=pics[1:],duration=[round((i+1)*1000/60)-round(i*1000/60) for i in range(88)],loop=0,lossless=True)
y,x=np.where(union);full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=[dict(clip=n,position=p,**measure(ST/'clips'/m['frames'][i]['file'])) for n,c in m['clips'].items() for p,i in enumerate(c['frames'])]
write(W/'measurements.json',metrics)
roster=read(R/'assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='dilophosaurus')
mm=ch['map_sync_metrics'];mm['full_fx_bbox_px']=full
mm['world_size_at_64ppu_m'].update(aura_w_m=round(full['w']/64,3),aura_h_m=round(full['h']/64,3))
mm['tile_32px_span'].update(full_fx_tiles_w=round(full['w']/32,3),full_fx_tiles_h=round(full['h']/32,3))
ch['motion_quality']=review;ch['qa_report']='docs/characters/dilophosaurus-motion-v2-qa.json'
for folder in ['clips','godot_bundle']:
 sidecars={p.relative_to(A/folder):p.read_bytes() for p in (A/folder).rglob('*.import')}
 shutil.rmtree(A/folder);shutil.copytree(ST/folder,A/folder)
 for rel,data in sidecars.items():
  if (A/folder/str(rel).removesuffix('.import')).exists():(A/folder/rel).write_bytes(data)
(A/'clips/.gdignore').touch();write(R/'assets/roster.json',roster);write(W/'review/keyframe-review.json',review)
qa={'character_id':'dilophosaurus','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':len(m['frames']),'clip_references':sum(len(c['frames']) for c in m['clips'].values()),'map_sync_metrics':mm,'render_contract':meta['render_contract'],'motion_quality':review,'technical_checks':'pending','frozen_clips':frozen,'protected_peer_files_unchanged':len(protected),'previous_owner_feedback':'Head/fans inflated rather than membranes undulating; idle held each pose500ms. Turn explicitly retained.'}
write(R/ch['qa_report'],qa)
s=read(R/'state.json'); now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_at']=now;s['project']['version']='0.9.1'
s['project']['version_history'].append({'version':'0.9.1','date':now,'summary':'Dilophosaurus idle/power motion correction; turn and all other clips/FX retained. Owner review pending.'})
s['current_focus'].update(status='motion_revision_installed_pending_checks',summary='Dilo motion-v2 installed; turn unchanged. Engine, browser and Owner review pending.');write(R/'state.json',s)
(R/'VERSION').write_text('0.9.1\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=R/f;p.write_text(p.read_text().replace('0.9.0','0.9.1'))
assert all(sha(R/p)==h for p,h in protected.items())
print(json.dumps({'atlas_sha256':digest,'frozen_clips':frozen,'protected_peer_files':len(protected),'full_fx':full}))
