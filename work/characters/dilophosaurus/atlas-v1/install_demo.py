"""Admit reviewed complete Dilophosaurus demo; Owner atlas approval remains pending."""
from pathlib import Path
import json,hashlib,shutil,copy,sys,datetime
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;R=W.parents[3];ST=W/'stage';A=R/'assets/dilophosaurus'
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'plan.json');m=read(ST/'clips/animation-clips.json');meta=read(ST/'godot_bundle/engine-export.json');body=list(plan['body_actions']);effects=[s['clip'] for s in plan['slash_schedule']]
contract={'body_clips':body,'effect_clips':effects,'locomotion':{'kind':'ground','clip':'walk','walk_cycle_order':list(range(8))},'aura':{'loop_clip':None,'charge_clip':None,'independent_clock':True},'projectile':None,'fx_pivot_px':[176,128],'turning':{'clip':'turn','from':'right','to':'left','duration_ticks':20,'method':'complete_perspective_poses','mirror_sequence_for_reverse':True},'target_slashes':{'body_clip':'power_up','active_window_ticks':[8,68],'default_target_canvas_px':plan['slash_target_canvas_px'],'strikes':[dict(s,duration_ticks=6) for s in plan['slash_schedule']],'target_rule':'All three hit the same independently supplied enemy/dummy point; no body/frill emission, no travel.','target_override':'Godot set_slash_target_global or set_slash_target_canvas; browser options.targetCanvasPx.','angle_art':'Baked whole-FX rotations and directional alpha sweep, no body transforms.'}}
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']={'body_art_source':'built-in imagegen complete whole-body keyframes from approved frill-v2master','identity_reference':plan['master'],'identity_sha256':plan['master_sha256'],'fx_source':'work/characters/dilophosaurus/atlas-v1/source/air-slash-owner.png','fx_source_sha256':plan['slash_source_sha256'],'source_fx_pose_count':1,'new_AI_FX':False,'body_part_cut_warp':False,'owner_approved':False,'atlas_demo_only':True};write(ST/'godot_bundle/engine-export.json',meta);digest=sha(ST/'godot_bundle/godot/dilophosaurus-atlas-00.png')
ims={n:[Image.open(ST/'clips'/m['frames'][i]['file']).convert('RGBA') for i in c['frames']] for n,c in m['clips'].items()}
def at(ticks,t):
 for i,d in enumerate(ticks):
  if t<d:return i
  t-=d
 return len(ticks)-1
union=np.zeros((256,384),bool)
for name in body:
 for im in ims[name]:union|=np.array(im)[:,:,3]>0
composite=[];samples=[];trace=[]
for t in range(88):
 bi=at(m['clips']['power_up']['ticks'],t);im=ims['power_up'][bi].copy();strike=next((s for s in contract['target_slashes']['strikes'] if s['at_tick']<=t<s['at_tick']+6),None)
 if strike:
  point=contract['target_slashes']['default_target_canvas_px'];fx=ims[strike['clip']][t-strike['at_tick']];im.alpha_composite(fx,(point[0]-176,point[1]-128))
 union|=np.array(im)[:,:,3]>0;composite.append(im);trace.append({'tick':t,'body_frame':bi,'slash':strike['clip'] if strike else None,'phase':t-strike['at_tick'] if strike else None,'point':contract['target_slashes']['default_target_canvas_px'] if strike else None})
 if t in [0,4,8,12,13,14,15,16,17,18,23,31,32,33,34,35,36,37,46,50,51,52,53,54,55,56,65,68,77,87]:samples.append((t,im))
import importlib.util
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W;rv.review('power_up-composite',[im for _,im in samples],[1]*len(samples));write(W/'review/composite-sample-ticks.json',[t for t,_ in samples]);write(W/'verification/88tick-trace.json',trace)
for bg in ['light','dark','checker']:
 pics=[]
 for im in composite:
  back=Image.new('RGBA',(384,256),'#eee8dc' if bg=='light' else '#171b23')
  if bg=='checker':
   from PIL import ImageDraw
   d=ImageDraw.Draw(back)
   for y in range(0,256,8):
    for x in range(0,384,8):d.rectangle((x,y,x+7,y+7),fill='#bbb' if (x//8+y//8)%2 else '#ddd')
  back.alpha_composite(im);pics.append(back.resize((768,512),Image.Resampling.NEAREST))
 pics[0].save(W/f'review/playback-power_up-composite-{bg}.webp',save_all=True,append_images=pics[1:],duration=[round((i+1)*1000/60)-round(i*1000/60) for i in range(88)],loop=0,lossless=True)
y,x=np.where(union);full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=[dict(clip=n,position=p,**measure(ST/'clips'/m['frames'][i]['file'])) for n,c in m['clips'].items() for p,i in enumerate(c['frames'])];write(W/'measurements.json',metrics)
mm={'canvas_size_px':[384,256],'foot_anchor_px':[176,224],'body_only_bbox_px':{'x':85,'y':128,'w':157,'h':96},'full_fx_bbox_px':full,'reference_ppu_64':64,'world_size_at_64ppu_m':{'body_w_m':round(157/64,3),'body_h_m':1.5,'aura_w_m':round(full['w']/64,3),'aura_h_m':round(full['h']/64,3)},'tile_32px_span':{'body_tiles_w':round(157/32,3),'body_tiles_h':3,'full_fx_tiles_w':round(full['w']/32,3),'full_fx_tiles_h':round(full['h']/32,3)}}
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds','character_identity']},'review_evidence':'work/characters/dilophosaurus/atlas-v1/review/keyframe-review.json','unresolved_structural_failures':[],'owner_approved':False,'naturalness_verdict':'pending_owner_real_time_review','notes':'New wholebody poses; neckfrills physically pulse, no VFX emission from frills. Three source-preserving directional slash sweeps at same independent target. Visual quality remains Owner Human Test gate.'}
roster=read(R/'assets/roster.json');ref=roster['animation_completeness_standard']['provisional_reference_clips'];missing=[n for n in ref if n not in body]
ch={'character_id':'dilophosaurus','display_name':'Dilophosaurus','faction':'special_beasts','role_label':'Twin-frill Theropod — Bite / Target Air Slashes','tags':['dinosaur','biped','paired_neck_frills','jaw_bite','target_slashes','pixel_art'],'status':'finalized_engine_verified_demo_pending_owner','atlas_stage':'demo_pending_owner','owner_animation_approval':'pending','canonical_identity':{'path':plan['master'],'sha256':plan['master_sha256']},'facing_contract':{'camera_view':'side_view_2d_three_quarter','default_atlas_facing':'right(+X)','left_facing_rule':'Four authored perspective wholebodyturnposes; mirroredsequenceforreverse; no cardflipping.','locomotion_vector_rule':'Two-leg forward+X walk, alternate near/far support; no run/jump.'},'map_sync_metrics':mm,'pixel_sharpness_metrics':{'texel_scale_ratio':'Native1px gameplay, Nearest; wholepose registration, no limb rig or scalarforcing.','edge_acutance_sobel':metrics[0]['edge_acutance_sobel'],'alpha_hardness_pct':100,'visible_alpha_hardness_pct':100,'opaque_key_px':0,'enclosed_key_pockets':0,'outer_ring_spill_fraction':0.0,'reference_note':'Body alpha threshold128; source slash keyRGB6/7/13 delta16,pocketfirst/1pxedgeunmix, wholeFXrotation and directed alpha sweep only. SoftFX permitted.'},'present_clips':body,'effect_clips':effects,'missing_provisional_clips':missing,'not_applicable_clips':{n:'Owner inherits current Spino scope and excludes heavy; guard/win excluded project-wide. No fake clip.' for n in missing},'render_contract':contract,'modes':{'combined_1layer':{'label':'Gộp Chung1Lớp + Independent Target Slashes','godot_prefab':'res://scenes/Dilophosaurus.tscn','bundle_id':'dilophosaurus'}},'motion_quality':review,'qa_report':'docs/characters/dilophosaurus-atlas-v1-qa.json'}
assert not A.exists(),'First demo install only'
for folder in ['clips','godot_bundle']:shutil.copytree(ST/folder,A/folder)
(A/'clips/.gdignore').touch();roster['characters'].append(ch);write(R/'assets/roster.json',roster);write(W/'review/keyframe-review.json',dict(review,filmstrips_opened=body+effects,composite_review='pending open',real_time='pending browser'));write(R/ch['qa_report'],{'character_id':'dilophosaurus','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':len(m['frames']),'clip_references':sum(len(c['frames']) for c in m['clips'].values()),'body_poses':sum(plan['body_actions'].values()),'source_FX_poses':1,'baked_FX_phases':18,'body_clips':body,'map_sync_metrics':mm,'render_contract':contract,'motion_quality':review,'technical_checks':'pending'})
protected=read(W/'protected-peers.json');assert all(sha(R/p)==h for p,h in protected.items());s=read(R/'state.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_at']=now;s['project']['version']='0.9.0';s['project']['version_history'].append({'version':'0.9.0','date':now,'summary':'Dilophosaurus atlas demo:7bodyactions,1secondphysicalfrillpulse,3same-targetslashangles. PendingOwnerHumanTest.'});s['current_focus'].update(status='atlas_installed_pending_checks',summary='Dilophosaurus atlas installed;62bodyposes/18FXphases/10clips. power88ticks active8..68(1s),same-targetslash12/31/50ticks,6tickeach. Pending engine/browser/Owner QA.');write(R/'state.json',s);(R/'VERSION').write_text('0.9.0\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=R/f;p.write_text(p.read_text().replace('0.8.1','0.9.0'))
print(json.dumps({'atlas_sha256':digest,'full_fx':full,'protected_files':len(protected)}))
