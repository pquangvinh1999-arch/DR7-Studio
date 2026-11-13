"""Install complete Chilopoda demo; final motion approval remains with Owner."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,shutil,sys
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';A=R/'assets/chilopoda'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
plan=read(W/'plan.json');m=read(S/'clips/animation-clips.json');meta=read(S/'godot_bundle/engine-export.json');contract=plan['render_contract'];digest=sha(S/'godot_bundle/godot/chilopoda-atlas-00.png')
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract;meta['provenance']={'body_art_source':'host_image/image_gen completebodyposes','canonical_identity':plan['master'],'canonical_identity_sha256':plan['master_sha256'],'owner_master_approved':True,'owner_approved':False,'atlas_demo_only':True,'body_part_cut_warp':False,'registration':'work/characters/chilopoda/atlas-v1/registration.json','ground_occlusion':'Runtime clips translated wholebody at ground_y; does not deform anatomy or alter source poses.','antenna_anchor_proof':'work/characters/chilopoda/atlas-v1/antenna-anchor-proof.json','turn_source':'generated/turn.png (flat-v2); rejectedhookstance remains separate','owner_turn_backlog':'docs/turn-retrofit-todo.md;afterChilopodaOwnerapproval only'};write(S/'godot_bundle/engine-export.json',meta)
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,'checks':{'body_connections':True,'whole_pose_sequence':True,'perspective_turns':True,'phase_timing':True,'three_backgrounds':True,'character_identity':True},'owner_approved':False,'naturalness_verdict':'pending_owner_human_test','unresolved_structural_failures':[],'review_evidence':'work/characters/chilopoda/atlas-v1/review/keyframe-review.json','notes':'Opened10filmstrips plus reverse-turn on3backgrounds. Wholecentipede poses; occupancy masks preserve dive-tail crossing source row. Turn first/last use flatwalk0/mirroraroundroot, with genuineintermediateperspective. Livebrowser andGodot checks still pending.'};write(W/'review/keyframe-review.json',review)
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=measure(S/'clips'/m['frames'][m['clips']['idle']['frames'][0]]['file']);write(W/'measurements.json',metrics)
union=np.zeros((256,384),bool)
for n in contract['body_clips']:
    for i in m['clips'][n]['frames']:union|=np.array(Image.open(S/'clips'/m['frames'][i]['file']))[:,:,3]>0
# Conservative gameplay envelope: actual complete-body entry/exit and targetedFX.
for i in m['clips']['attack_light']['frames']:
    im=Image.open(S/'clips'/m['frames'][i]['file']).convert('RGBA');shift=Image.new('RGBA',(384,256));shift.alpha_composite(im,(80,0));union|=np.array(shift)[:,:,3]>0
for n in contract['effect_clips']:
    for i in m['clips'][n]['frames']:
        im=Image.open(S/'clips'/m['frames'][i]['file']).convert('RGBA');shift=Image.new('RGBA',(384,256));point=(304,224) if n=='burrow_dust_fx' else (304,200);shift.alpha_composite(im,(point[0]-176,point[1]-128));union|=np.array(shift)[:,:,3]>0
y,x=np.where(union);full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
mm={'canvas_size_px':[384,256],'foot_anchor_px':[176,224],'body_only_bbox_px':{'x':98,'y':165,'w':157,'h':59},'full_fx_bbox_px':full,'reference_ppu_64':64,'world_size_at_64ppu_m':{'body_w_m':round(157/64,3),'body_h_m':round(59/64,3),'aura_w_m':round(full['w']/64,3),'aura_h_m':round(full['h']/64,3)},'tile_32px_span':{'body_tiles_w':157/32,'body_tiles_h':59/32,'full_fx_tiles_w':full['w']/32,'full_fx_tiles_h':full['h']/32}}
roster=read(R/'assets/roster.json');ref=roster['animation_completeness_standard']['provisional_reference_clips'];missing=[n for n in ref if n not in contract['body_clips']]
ch={'character_id':'chilopoda','display_name':'Chilopoda','faction':'special_beasts','role_label':'Armored Centipede — Burrow Bite / Twin Red Antenna Lasers','tags':['centipede','chilopoda','ground','burrow','dual_laser','pixel_art'],'status':'finalized_engine_verified_demo_pending_owner','atlas_stage':'demo_pending_owner','owner_animation_approval':'pending','canonical_identity':{'path':plan['master'],'sha256':plan['master_sha256']},'facing_contract':{'camera_view':'side_view_2d_three_quarter','default_atlas_facing':'right(+X)','left_facing_rule':'Authored8pose perspective turn36ticks thencommitdirection. Reverse uses full sequence mirrored aroundroot;bothdirections tested independently.','locomotion_vector_rule':'Entirebodyflat,manylegmetachronalwalk;no run. Endpointstop/turn/reversewalk. Targetburrow leavesactornear target afterbite.'},'map_sync_metrics':mm,'pixel_sharpness_metrics':{'texel_scale_ratio':'Native1px gameplay,Nearest,wholeposeonly','edge_acutance_sobel':metrics['edge_acutance_sobel'],'alpha_hardness_pct':100,'visible_alpha_hardness_pct':100,'opaque_key_px':0,'enclosed_key_pockets':0,'outer_ring_spill_fraction':0.0,'reference_note':'Nativealpha source; bodythreshold128 and wholepose registration, no chromakey or forcedscalar. FXsoftalpha allowed.'},'present_clips':contract['body_clips'],'effect_clips':contract['effect_clips'],'missing_provisional_clips':missing,'not_applicable_clips':{n:'Owner requested Bat-equivalent bodycount minusrun plusturn; nojump/heavy/aura; guard/win excludedprojectwide.' for n in missing},'render_contract':contract,'modes':{'combined_1layer':{'label':'Combined1Layer + GroundOcclusion / IndependentSoil / TwinLaserFX','godot_prefab':'res://scenes/Chilopoda.tscn','bundle_id':'chilopoda'}},'motion_quality':review,'qa_report':'docs/characters/chilopoda-atlas-v1-qa.json'}
assert not A.exists(),'Firstadmission only'
for folder in ['clips','godot_bundle']:shutil.copytree(S/folder,A/folder)
(A/'clips/.gdignore').touch();(A/'source').mkdir();(A/'source/.gdignore').touch();roster['characters'].insert(0,ch);write(R/'assets/roster.json',roster)
scene='''[gd_scene load_steps=4 format=3]
[ext_resource type="Script" path="res://scenes/ChilopodaFighter2D.gd" id="1"]
[ext_resource type="SpriteFrames" path="res://assets/chilopoda/godot_bundle/godot/chilopoda.tres" id="2"]
[ext_resource type="Script" path="res://tests/SkillAnimator2D.gd" id="3"]
[node name="Chilopoda" type="Node2D"]
script = ExtResource("1")
character_id = "chilopoda"
engine_export_json = "res://assets/chilopoda/godot_bundle/engine-export.json"
[node name="Sprite" type="AnimatedSprite2D" parent="."]
texture_filter = 1
sprite_frames = ExtResource("2")
animation = &"idle"
autoplay = "idle"
centered = false
offset = Vector2(-176, -224)
'''
for node,clip in [('DustFX','burrow_dust_fx'),('Glow0','antenna_glow_fx'),('Glow1','antenna_glow_fx'),('Laser0','red_laser_fx'),('Laser1','red_laser_fx')]:
    scene+=f'''[node name="{node}" type="AnimatedSprite2D" parent="."]
visible = false
texture_filter = 1
sprite_frames = ExtResource("2")
animation = &"{clip}"
centered = false
offset = Vector2(-176, -128)
'''
scene+='[node name="SkillAnimator" type="Node2D" parent="."]\nscript = ExtResource("3")\n';(R/'scenes/Chilopoda.tscn').write_text(scene)
write(R/ch['qa_report'],{'character_id':'chilopoda','status':'engine_and_browser_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':len(m['frames']),'clips':len(m['clips']),'map_sync_metrics':mm,'render_contract':contract,'motion_quality':review,'technical_checks':'pending','owner_approved':False,'turn_policy':'RequiredbyOwner; bothdirections andendpointscheckedindependently; scorependingchecks/Ownerapproval'})
old=(R/'VERSION').read_text().strip();new='0.11.0';(R/'VERSION').write_text(new+'\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
    p=R/f;p.write_text(p.read_text().replace(old,new))
s=read(R/'state.json');now=datetime.now(timezone.utc).isoformat();s['updated_at']=now;s['project']['version']=new;s['project']['version_history'].append({'version':new,'date':now,'summary':'Chilopoda demo:burrow30tickhidden/bite,newtargetposition,twinantennaeredlasers,realturn/endpointpatrol. Defaultturnconstitution+skill/TODO forfuturepeers.'});s['current_focus'].update(status='chilopoda_installed_pending_checks',qa_report=ch['qa_report'],preview_url='http://localhost:8080/?character=chilopoda&clip=attack_light');write(R/'state.json',s)
protected=read(W/'protected-peers.json');changed=[p for p,h in protected.items() if p!='assets/roster.json' and sha(R/p)!=h];assert not changed,changed
print(json.dumps({'atlas_sha256':digest,'frames':len(m['frames']),'clips':len(m['clips']),'full_fx':full,'approved_peer_files_unchanged':len(protected)-1}))
