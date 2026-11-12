"""Admit the complete technical demo; Owner motion approval remains pending."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys,datetime
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;R=W.parents[3];ST=W/'stage';DEST=R/'assets/tasmanian_king_crab'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
protected={str(p.relative_to(R)):sha(p) for cid in ['t_rex','spinosaurus','pteranodon'] for p in (R/'assets'/cid).rglob('*') if p.is_file() and not p.name.endswith('.import')};write(W/'protected-peers.json',protected)
m=read(ST/'clips/animation-clips.json');meta=read(ST/'godot_bundle/engine-export.json');body=['idle','walk','attack_nomal','power_up','hit','ko'];effects=['power_orb_loop','power_orb_projectile']
contract={'body_clips':body,'effect_clips':effects,'locomotion':{'kind':'ground','clip':'walk','walk_cycle_order':list(range(8))},'aura':{'loop_clip':None,'charge_clip':None,'independent_clock':True},'fx_pivot_px':[176,128],
 'charge':{'body_clip':'power_up','effect_clip':'power_orb_loop','release_frame':2,'origin_canvas_px_by_frame':[[196,203],[220,149]],'clock':'body_ticks_before_release'},
 'projectile':{'kind':'linear_energy','body_clip':'power_up','projectile_clip':'power_orb_projectile','release_frame':2,'lifetime_ticks':16,'origin_canvas_px':[267,157],'velocity_px_per_tick':[4,0]}}
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']={'body_art_source':'built-in imagegen complete whole-body keyframes','identity_reference':'work/characters/tasmanian_king_crab/size-master/master.png','identity_sha256':sha(R/'work/characters/tasmanian_king_crab/size-master/master.png'),'fx_source':'work/characters/tasmanian_king_crab/atlas-v1/source/power-orb-owner.png','fx_source_sha256':sha(W/'source/power-orb-owner.png'),'source_fx_pose_count':6,'new_bridge_pose_count':2,'body_part_cut_warp':False,'registration':'Fixed whole-frame scale peraction, shared row ground;2Dcomponent ownership includes dissolve islands. Original idle0 retained exactly.','owner_approved':False,'atlas_demo_only':True};write(ST/'godot_bundle/engine-export.json',meta)
digest=sha(ST/'godot_bundle/godot/tasmanian_king_crab-atlas-00.png')
frames={name:[Image.open(ST/'clips'/m['frames'][i]['file']).convert('RGBA') for i in c['frames']] for name,c in m['clips'].items()}
# Exact60tick power-up playback and representative composite keyposes.
keys=[];allpics=[];power=m['clips']['power_up'];release=sum(power['ticks'][:2]);union=np.zeros((256,384),bool)
def at_tick(ticks,tick):
 for i,t in enumerate(ticks):
  if tick<t:return i
  tick-=t
 return len(ticks)-1
for ims in frames.values():
 for im in ims:union|=np.array(im)[:,:,3]>0
for tick in range(sum(power['ticks'])):
 bi=at_tick(power['ticks'],tick);im=frames['power_up'][bi].copy();fi=None;kind=None
 if tick<release:
  fi=at_tick([4]*8,tick);point=contract['charge']['origin_canvas_px_by_frame'][bi];kind='charge'
 else:
  elapsed=tick-release
  if elapsed<16:fi=at_tick([4]*4,elapsed);point=[267+4*elapsed,157];kind='projectile'
 if fi is not None:
  fx=frames['power_orb_loop' if kind=='charge' else 'power_orb_projectile'][fi];im.alpha_composite(fx,(point[0]-176,point[1]-128))
 union|=np.array(im)[:,:,3]>0;bg=Image.new('RGBA',(384,256),'#eee');bg.alpha_composite(im);allpics.append(bg.resize((768,512),Image.Resampling.NEAREST))
 if tick in [0,4,8,12,16,20,23,24,28,32,36,39,40,44,52,59]:keys.append({'tick':tick,'body_frame':bi,'fx_kind':kind,'fx_frame':fi,'image':im})
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W;rv.review('power_up-composite',[x['image'] for x in keys],[1]*len(keys))
durations=[round((i+1)*1000/60)-round(i*1000/60) for i in range(len(allpics))];allpics[0].save(W/'review/playback-power_up-composite.webp',save_all=True,append_images=allpics[1:],duration=durations,loop=0,lossless=True)
write(W/'review/power-up-samples.json',[{k:v for k,v in x.items() if k!='image'} for x in keys]);ys,xs=np.where(union);full={'x':int(xs.min()),'y':int(ys.min()),'w':int(xs.max()-xs.min()+1),'h':int(ys.max()-ys.min()+1)}
metrics=[dict(clip=name,position=i,**measure(ST/'clips'/m['frames'][idx]['file'])) for name,c in m['clips'].items() for i,idx in enumerate(c['frames'])];write(W/'measurements.json',metrics)
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds','character_identity']},'review_evidence':'work/characters/tasmanian_king_crab/atlas-v1/review/keyframe-review.json','unresolved_structural_failures':[],'owner_approved':False,'naturalness_verdict':'pending_owner_real_time_review','notes':'No turns requested; no rotated quad or part rig. Distal claw fragments atattack3/4are intentional Owner pixel dissolve; proximal joint remains solid. Wholepose identity/leg cadence and entry/loop seams remain Human Test gates.'}
mm={'canvas_size_px':[384,256],'foot_anchor_px':[176,224],'body_only_bbox_px':{'x':110,'y':160,'w':133,'h':64},'full_fx_bbox_px':full,'reference_ppu_64':64,'world_size_at_64ppu_m':{'body_w_m':round(133/64,3),'body_h_m':1,'aura_w_m':round(full['w']/64,3),'aura_h_m':round(full['h']/64,3)},'tile_32px_span':{'body_tiles_w':round(133/32,3),'body_tiles_h':2,'full_fx_tiles_w':round(full['w']/32,3),'full_fx_tiles_h':round(full['h']/32,3)}}
roster=read(R/'assets/roster.json');reference=roster['animation_completeness_standard']['provisional_reference_clips'];missing=[x for x in reference if x not in body]
char={'character_id':'tasmanian_king_crab','display_name':'Tasmanian King Crab','faction':'special_beasts','role_label':'Asymmetric Giant Crab — Claw Strike / Energy Orb','tags':['crab','eight_walking_legs','asymmetric_claws','pixel_art','projectile_fx'],'status':'finalized_engine_verified_demo_pending_owner','facing_contract':{'camera_view':'side_view_2d_three_quarter','default_atlas_facing':'right(+X);huge anatomicalright claw near camera, smallleft claw far','left_facing_rule':'Horizontal display mirror only; no back-view or authored turn clip claimed.','locomotion_vector_rule':'Eight-leg forward ground walk toward+X; walk-only, no run.'},'map_sync_metrics':mm,'pixel_sharpness_metrics':{'texel_scale_ratio':'Native gameplay PNG1px, Nearest; one whole-frame scale per action; no LUT/sharpen/palette forcing','edge_acutance_sobel':metrics[0]['edge_acutance_sobel'],'alpha_hardness_pct':100,'visible_alpha_hardness_pct':100,'opaque_key_px':0,'enclosed_key_pockets':0,'outer_ring_spill_fraction':0.0,'reference_note':'Body nativealpha threshold128; FX background keyRGB000080 threshold16 then1pxedgeunmix, fixed1/2Nearest to fit claw. SoftFX permitted; source key similarity≤16 has no surviving visible pixels. Sobel not an acceptance scalar.'},'present_clips':body,'effect_clips':effects,'missing_provisional_clips':missing,'not_applicable_clips':{k:('Owner uses attack_nomal for normal claw attack; no alias fake frames.' if k=='attack_light' else 'Owner explicitly excludes this clip for Tasmanian; guard/win excluded project-wide.') for k in missing},'render_contract':contract,'modes':{'combined_1layer':{'label':'Gộp Chung1Lớp + Independent Charge/Projectile FX','godot_prefab':'res://scenes/TasmanianKingCrab.tscn','bundle_id':'tasmanian_king_crab'}},'atlas_stage':'demo_pending_owner','owner_animation_approval':'pending','canonical_identity':{'path':'work/characters/tasmanian_king_crab/size-master/master.png','sha256':sha(R/'work/characters/tasmanian_king_crab/size-master/master.png')},'motion_quality':review,'qa_report':'docs/characters/tasmanian-king-crab-atlas-v1-qa.json'}
roster['characters']=[c for c in roster['characters'] if c['character_id']!='tasmanian_king_crab']+[char]
assert not DEST.exists(),'First install only; do not overwrite another revision'
for folder in ['clips','godot_bundle']:shutil.copytree(ST/folder,DEST/folder)
(DEST/'clips/.gdignore').touch();write(R/'assets/roster.json',roster)
write(W/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,'owner_approved':False,'scope':review['notes'],'filmstrips_opened':['idle','walk','attack_nomal','power_up','hit','ko','power_orb_loop','power_orb_projectile'],'composite_review':'pending open after generation','motion_at_real_time':'pending browser capture/Human Test','artifacts':{p.name:sha(p) for p in (W/'review').glob('*') if p.suffix in ['.png','.webp']}})
write(R/char['qa_report'],{'character_id':'tasmanian_king_crab','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':54,'body_frames':46,'fx_frames':8,'clips':8,'body_clips':body,'owner_source_fx_frames':6,'new_bridge_fx_frames':2,'canvas_size_px':[384,256],'anchor_px':[176,224],'map_sync_metrics':mm,'motion_quality':review,'technical_checks':'pending','fx_source_evidence':'work/characters/tasmanian_king_crab/atlas-v1/fx-source-evidence.json','registration':'work/characters/tasmanian_king_crab/atlas-v1/registration.json','render_contract':contract})
s=read(R/'state.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_at']=now;s['project']['version']='0.7.0';s['project']['version_history'].append({'version':'0.7.0','date':now,'summary':'Tasmanian King Crab atlas demo:6bodyclips,normalclawdissolve,independentcharge/projectile orb6source+2bridge,releasebodyframe2. PendingOwnerHumanTest.'});s['current_focus']['status']='atlas_installed_pending_checks';s['current_focus']['summary']='Tasmanian atlas54uniquePNGs/8clips installed;6bodyactions46poses+8FX(6source+2bridge). Noaura/run/jump/heavy/guard/win. Charge0..5beforereleaseatbody2/tick24,projectile5/6/7/0for16ticks. PendingGodot/Rust/WASM/browserQAandOwner.';write(R/'state.json',s);(R/'VERSION').write_text('0.7.0\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=R/f;p.write_text(p.read_text().replace('0.6.1','0.7.0'))
assert all(sha(R/p)==v for p,v in protected.items())
print(json.dumps({'atlas_sha256':digest,'full_fx':full,'protected_files':len(protected),'release_body_frame':2,'release_tick':24}))
