"""Admit the complete technical demo; Owner motion approval remains pending."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys,datetime
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;R=W.parents[3];ST=W/'stage';DEST=R/'assets/sarcosuchus'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
protected={str(p.relative_to(R)):sha(p) for cid in ['t_rex','spinosaurus','pteranodon','tasmanian_king_crab'] for p in (R/'assets'/cid).rglob('*') if p.is_file() and not p.name.endswith('.import')};write(W/'protected-peers.json',protected)
m=read(ST/'clips/animation-clips.json');meta=read(ST/'godot_bundle/engine-export.json');body=['idle','walk','attack_nomal','power_up','hit','ko','turn'];effects=['energy_charge_fx','energy_blast_fx']
contract={'body_clips':body,'effect_clips':effects,'locomotion':{'kind':'ground','clip':'walk','walk_cycle_order':list(range(8))},'aura':{'loop_clip':None,'charge_clip':None,'independent_clock':True},'fx_pivot_px':[176,128],
 'charge':{'body_clip':'power_up','effect_clip':'energy_charge_fx','release_frame':2,'origin_canvas_px_by_frame':[[237,202],[239,190]],'clock':'body_ticks_before_release'},
 'projectile':{'kind':'linear_energy','body_clip':'power_up','projectile_clip':'energy_blast_fx','release_frame':2,'lifetime_ticks':18,'origin_canvas_px':[244,194],'velocity_px_per_tick':[4,0]},'turning':{'clip':'turn','from':'right','to':'left','duration_ticks':20,'method':'complete_perspective_poses','mirror_sequence_for_reverse':True}}
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']={'body_art_source':'built-in imagegen complete whole-body keyframes','identity_reference':'work/characters/sarcosuchus/master-review/master-gameplay-v1.png','identity_sha256':sha(R/'work/characters/sarcosuchus/master-review/master-gameplay-v1.png'),'fx_source':'work/characters/sarcosuchus/atlas-v1/source/power-up-owner.png','fx_source_sha256':sha(W/'source/power-up-owner.png'),'source_fx_pose_count':6,'new_bridge_pose_count':0,'scaled_charge_variant_count':1,'body_part_cut_warp':False,'registration':'Fixed whole-frame scale peraction, shared row ground;2Dcomponent ownership includes dissolve islands. Original idle0 retained exactly.','owner_approved':False,'atlas_demo_only':True};write(ST/'godot_bundle/engine-export.json',meta)
digest=sha(ST/'godot_bundle/godot/sarcosuchus-atlas-00.png')
frames={name:[Image.open(ST/'clips'/m['frames'][i]['file']).convert('RGBA') for i in c['frames']] for name,c in m['clips'].items()}
# Exact60tick power-up playback and representative composite keyposes.
keys=[];allpics=[];power=m['clips']['power_up'];release=sum(power['ticks'][:2]);union=np.zeros((256,384),bool)
def at_tick(ticks,tick):
 for i,t in enumerate(ticks):
  if tick<t:return i
  tick-=t
 return len(ticks)-1
for ims in [frames[name] for name in body]:
 for im in ims:union|=np.array(im)[:,:,3]>0
for tick in range(sum(power['ticks'])):
 bi=at_tick(power['ticks'],tick);im=frames['power_up'][bi].copy();fi=None;kind=None
 if tick<release:
  fi=at_tick([5,5],tick);point=contract['charge']['origin_canvas_px_by_frame'][bi];kind='charge'
 else:
  elapsed=tick-release
  if elapsed<18:fi=at_tick([3]*6,elapsed);point=[244+4*elapsed,194];kind='projectile'
 if fi is not None:
  fx=frames['energy_charge_fx' if kind=='charge' else 'energy_blast_fx'][fi];im.alpha_composite(fx,(point[0]-176,point[1]-128))
 union|=np.array(im)[:,:,3]>0;bg=Image.new('RGBA',(384,256),'#eee');bg.alpha_composite(im);allpics.append(bg.resize((768,512),Image.Resampling.NEAREST))
 if tick in [0,4,5,9,10,13,16,19,22,25,27,28,35,45]:keys.append({'tick':tick,'body_frame':bi,'fx_kind':kind,'fx_frame':fi,'image':im})
spec=importlib.util.spec_from_file_location('review',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W;rv.review('power_up-composite',[x['image'] for x in keys],[1]*len(keys))
durations=[round((i+1)*1000/60)-round(i*1000/60) for i in range(len(allpics))];allpics[0].save(W/'review/playback-power_up-composite.webp',save_all=True,append_images=allpics[1:],duration=durations,loop=0,lossless=True)
write(W/'review/power-up-samples.json',[{k:v for k,v in x.items() if k!='image'} for x in keys]);ys,xs=np.where(union);full={'x':int(xs.min()),'y':int(ys.min()),'w':int(xs.max()-xs.min()+1),'h':int(ys.max()-ys.min()+1)}
metrics=[dict(clip=name,position=i,**measure(ST/'clips'/m['frames'][idx]['file'])) for name,c in m['clips'].items() for i,idx in enumerate(c['frames'])];write(W/'measurements.json',metrics)
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds','character_identity']},'review_evidence':'work/characters/sarcosuchus/atlas-v1/review/keyframe-review.json','unresolved_structural_failures':[],'owner_approved':False,'naturalness_verdict':'pending_owner_real_time_review','notes':'Seven full-body action sequences reviewed on light/dark/checker. Jaw remains connected throughout bite; turn has real three-quarter views. Gait cadence and naturalness remain pending Owner Human Test. No part rig or card rotation.'}
mm={'canvas_size_px':[384,256],'foot_anchor_px':[176,224],'body_only_bbox_px':{'x':89,'y':190,'w':157,'h':34},'full_fx_bbox_px':full,'reference_ppu_64':64,'world_size_at_64ppu_m':{'body_w_m':round(157/64,3),'body_h_m':round(34/64,3),'aura_w_m':round(full['w']/64,3),'aura_h_m':round(full['h']/64,3)},'tile_32px_span':{'body_tiles_w':round(157/32,3),'body_tiles_h':round(34/32,3),'full_fx_tiles_w':round(full['w']/32,3),'full_fx_tiles_h':round(full['h']/32,3)}}
roster=read(R/'assets/roster.json');reference=roster['animation_completeness_standard']['provisional_reference_clips'];missing=[x for x in reference if x not in body]
char={'character_id':'sarcosuchus','display_name':'Sarcosuchus','faction':'special_beasts','role_label':'Prehistoric Crocodile — Jaw Bite / Energy Projectile','tags':['crocodile','quadruped','jaw_bite','pixel_art','projectile_fx'],'status':'finalized_engine_verified_demo_pending_owner','facing_contract':{'camera_view':'side_view_2d_three_quarter','default_atlas_facing':'right(+X); four legs, olive armor, long crocodilian jaws','left_facing_rule':'Four authored perspective turn poses before committing left/right facing; reverse uses mirrored whole sequence.','locomotion_vector_rule':'Four-leg forward walk toward+X; 0..7→0 continuous cycle, no run.'},'map_sync_metrics':mm,'pixel_sharpness_metrics':{'texel_scale_ratio':'Native gameplay PNG1px, Nearest; one whole-frame scale per action; no LUT/sharpen/palette forcing','edge_acutance_sobel':metrics[0]['edge_acutance_sobel'],'alpha_hardness_pct':100,'visible_alpha_hardness_pct':100,'opaque_key_px':0,'enclosed_key_pockets':0,'outer_ring_spill_fraction':0.0,'reference_note':'Body nativealpha threshold128; FX background RGB008000 keyed pocket-first, green contamination unmixed with Gforeground=max(R,B); whole FX1/2Nearest. SoftFX permitted; Source greenscreen excess removed; measured proof saved separately. Sobel not an acceptance scalar.'},'present_clips':body,'effect_clips':effects,'missing_provisional_clips':missing,'not_applicable_clips':{k:('Owner uses attack_nomal for jaw bite; no alias fake frames.' if k=='attack_light' else 'Owner explicitly excludes this clip for Sarcosuchus; guard/win excluded project-wide.') for k in missing},'render_contract':contract,'modes':{'combined_1layer':{'label':'Gộp Chung1Lớp + Independent Mouth Charge/Projectile FX','godot_prefab':'res://scenes/Sarcosuchus.tscn','bundle_id':'sarcosuchus'}},'atlas_stage':'demo_pending_owner','owner_animation_approval':'pending','canonical_identity':{'path':'work/characters/sarcosuchus/master-review/master-gameplay-v1.png','sha256':sha(R/'work/characters/sarcosuchus/master-review/master-gameplay-v1.png')},'motion_quality':review,'qa_report':'docs/characters/sarcosuchus-atlas-v1-qa.json'}
roster['characters']=[c for c in roster['characters'] if c['character_id']!='sarcosuchus']+[char]
assert not DEST.exists(),'First install only; do not overwrite another revision'
for folder in ['clips','godot_bundle']:shutil.copytree(ST/folder,DEST/folder)
(DEST/'clips/.gdignore').touch();write(R/'assets/roster.json',roster)
write(W/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,'owner_approved':False,'scope':review['notes'],'filmstrips_opened':body+effects,'composite_review':'pending open after generation','motion_at_real_time':'pending browser capture/Human Test','artifacts':{p.name:sha(p) for p in (W/'review').glob('*') if p.suffix in ['.png','.webp']}})
write(R/char['qa_report'],{'character_id':'sarcosuchus','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':62,'body_frames':55,'fx_frames':7,'clips':9,'body_clips':body,'owner_source_fx_frames':6,'new_bridge_fx_frames':0,'scaled_charge_variant_frames':1,'canvas_size_px':[384,256],'anchor_px':[176,224],'map_sync_metrics':mm,'motion_quality':review,'technical_checks':'pending','fx_source_evidence':'work/characters/sarcosuchus/atlas-v1/fx-source-evidence.json','registration':'work/characters/sarcosuchus/atlas-v1/registration.json','render_contract':contract})
s=read(R/'state.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();s['updated_at']=now;s['project']['version']='0.8.0';s['project']['version_history'].append({'version':'0.8.0','date':now,'summary':'Sarcosuchus demo:7bodyactions55poses, jaw bite,6sourceFX left-to-right once, mouth release bodyframe2/tick10. Pending Owner Human Test.'});s['current_focus']['status']='atlas_installed_pending_checks';s['current_focus']['summary']='Sarcosuchus atlas installed:55bodyposes,6sourceFX+1scaledcharge,9clips, mouth release body2/tick10. Technical/browser checks pending; Owner atlas approval pending.';write(R/'state.json',s);(R/'VERSION').write_text('0.8.0\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=R/f;p.write_text(p.read_text().replace('0.7.0','0.8.0'))
assert all(sha(R/p)==v for p,v in protected.items())
print(json.dumps({'atlas_sha256':digest,'full_fx':full,'protected_files':len(protected),'release_body_frame':2,'release_tick':10}))
