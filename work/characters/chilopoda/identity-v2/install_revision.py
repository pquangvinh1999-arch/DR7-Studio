"""Install the identity revision, retaining Owner gameplay contracts and other characters."""
from pathlib import Path
import json,hashlib,shutil,sys
from datetime import datetime,timezone
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';A=R/'assets/chilopoda'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
plan=read(W/'plan.json');m=read(S/'clips/animation-clips.json');meta=read(S/'godot_bundle/engine-export.json');contract=plan['render_contract'];digest=sha(S/'godot_bundle/godot/chilopoda-atlas-00.png')
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract
meta['provenance']={'body_art_source':'built-in image_gen, complete body poses','canonical_identity':plan['master'],'canonical_identity_sha256':plan['master_sha256'],'owner_master_approved':True,'owner_approved':False,'atlas_demo_only':True,'body_part_cut_warp':False,'registration':'work/characters/chilopoda/identity-v2/registration.json','identity_revision':plan['identity_revision'],'turn_source':'New complete walk and attack poses, runtime changes facing only while fully hidden; no visible cardflip.'}
write(S/'godot_bundle/engine-export.json',meta)
for folder in ['clips','godot_bundle']:
 shutil.rmtree(A/folder);shutil.copytree(S/folder,A/folder)
(A/'clips/.gdignore').touch()
roster=read(R/'assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='chilopoda')
ch['canonical_identity']={'path':plan['master'],'sha256':plan['master_sha256'],'owner_approval':plan['identity_revision']['canonical_approval']};ch['render_contract']=contract
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,'checks':{'body_connections':True,'whole_pose_sequence':True,'perspective_turns':False,'burrow_turn_bidirectional':True,'phase_timing':True,'three_backgrounds':True,'character_identity':True},'not_applicable_checks':{'perspective_turns':'Owner approved burrow/reorient/emerge in place instead of surface rotation.'},'owner_approved':False,'naturalness_verdict':'pending_owner_human_test','unresolved_structural_failures':[],'review_evidence':'work/characters/chilopoda/identity-v2/review/identity-review.json','notes':'New complete-pose action sheets reviewed on light/dark/checker against selected power_up1. Earlier oversized-head render and truncated dive heads rejected and regenerated. Original power1..10 retained. Canonical ready poses use exact selected master; no old master injection. Runtime checks and wall-clock observations recorded separately.'}
ch['motion_quality']=review;ch['status']='finalized_demo_pending_owner';ch['qa_report']='docs/characters/chilopoda-identity-v2-qa.json'
mm=ch['map_sync_metrics'];mm['body_only_bbox_px']={'x':98,'y':154,'w':160,'h':70};mm['world_size_at_64ppu_m'].update(body_w_m=2.5,body_h_m=round(70/64,3));mm['tile_32px_span'].update(body_tiles_w=5,body_tiles_h=70/32)
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=measure(W/'canonical/master.png');write(W/'measurements.json',metrics);ch['pixel_sharpness_metrics']['edge_acutance_sobel']=metrics['edge_acutance_sobel'];write(R/'assets/roster.json',roster)
write(W/'review/identity-review.json',review);write(R/ch['qa_report'],{'character_id':'chilopoda','status':'identity_revision_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':len(m['frames']),'clips':len(m['clips']),'canonical_identity':ch['canonical_identity'],'render_contract':contract,'map_sync_metrics':mm,'motion_quality':review,'technical_checks':'pending','owner_approved':False,'identity_revision':plan['identity_revision']})
old=(R/'VERSION').read_text().strip();new='0.11.1';(R/'VERSION').write_text(new+'\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=R/f;p.write_text(p.read_text().replace(old,new))
s=read(R/'state.json');now=datetime.now(timezone.utc).isoformat();s['updated_at']=now;s['project']['version']=new
if not any(h['version']==new for h in s['project']['version_history']):s['project']['version_history'].append({'version':new,'date':now,'summary':'Owner-selected Chilopoda power_up1 promoted as exact canonical; all body actions regenerated to match, old master removed from ready poses. Gameplay timing/FX/turn contracts preserved.'})
s['current_focus'].update(status='identity_revision_installed_pending_checks',atlas_plan=str((W/'plan.json').relative_to(R)),qa_report=ch['qa_report']);write(R/'state.json',s)
protected=read(W.parent/'atlas-v1/protected-peers.json');changed=[p for p,h in protected.items() if p!='assets/roster.json' and sha(R/p)!=h];assert not changed,changed
write(W/'repair-attempts.json',{'issue_id':'CHILO-IDENTITY-POWER1','max_cycles':5,'status':'pending_verification','source_review_iterations':['First generation rejected: overly large armor/head; used exact high-resolution power1 progenitor for repair','Dive source head truncation regenerated as complete connected heads before packaging'],'loop_attempts':[]})
print(json.dumps({'atlas_sha256':digest,'master_sha256':plan['master_sha256'],'frames':len(m['frames']),'clips':len(m['clips']),'protected_peer_files_unchanged':len(protected)-1,'version':new}))
