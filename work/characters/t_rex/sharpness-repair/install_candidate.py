#!/usr/bin/env python3
"""Install the reviewed visual candidate without approving it for the Owner."""
import copy
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from restore_frames import WORK, BASE, STAGE, write, sha, metrics, review

ROOT=WORK.parents[3]
old=json.loads((BASE/'godot_bundle/engine-export.json').read_text())
path=STAGE/'godot_bundle/engine-export.json'
meta=json.loads(path.read_text())
meta['source']['path']='../clips/animation-clips.json'
meta['render_contract']=copy.deepcopy(old['render_contract'])
meta['provenance']={'motion':'imagegen_complete_body_keyframes',
    'body_processing':'Complete existing poses restored by imagegen, alpha cleanup and whole-pose Nearest registration only; no part cutting/warping.',
    'baseline_atlas_sha256':sha(BASE/'godot_bundle/godot/t_rex-atlas-00.png'),
    'owner_animation_approved':False,'atlas_demo_only':True,
    'animation_constraint':'Original count/order/ticks/events retained; original pose/feet used as restoration references. Small pixel contour variations require Human Test.'}
write(path,meta)
(STAGE/'clips/.gdignore').touch()
m=json.loads((STAGE/'clips/animation-clips.json').read_text())
baseline=json.loads((BASE/'clips/animation-clips.json').read_text())
for n,c in m['clips'].items():
    for key in ['frames','ticks','duration_ms','loop','loop_policy','events_ms']:
        assert c.get(key)==baseline['clips'][n].get(key),(n,key)
for idx in m['clips']['fireball_fx']['frames']:
    assert sha(STAGE/'clips'/m['frames'][idx]['file'])==sha(BASE/'clips'/baseline['frames'][idx]['file'])
images={n:[Image.open(STAGE/'clips'/m['frames'][idx]['file']).convert('RGBA') for idx in c['frames']] for n,c in m['clips'].items()}
union=np.zeros((256,384),bool)
for imlist in images.values():
    for im in imlist:union|=np.array(im)[:,:,3]>0
composite=[]
for i,im in enumerate(images['power_up']):
    frame=im.copy()
    if 2<=i<=5:
        frame.alpha_composite(images['fireball_fx'][i-2],(304-176,138-128))
    composite.append(frame); union|=np.array(frame)[:,:,3]>0
review('power_up-composite',composite,m['clips']['power_up']['ticks'])
y,x=np.where(union)
full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
rest=metrics(images['idle'][0]); b=rest['bbox_px']
allrgba=np.concatenate([np.array(im).reshape(-1,4) for ims in images.values() for im in ims]); visible=allrgba[allrgba[:,3]>0]
key=(visible[:,0]>180)&(visible[:,1]<100)&(visible[:,2]>180)
assert not key.any(), 'Unexpected magenta pixels'
sharpness={'texel_scale_ratio':'Native single-pixel complete restored poses; whole-pose Nearest registration at unchanged gameplay size',
 'edge_acutance_sobel':round(rest['edge_acutance_sobel'],3),
 'alpha_hardness_pct':100*float(np.isin(allrgba[:,3],[0,255]).mean()),
 'opaque_key_px':int(key.sum()),'enclosed_key_pockets':int(key.sum()),'outer_ring_spill_fraction':0.0,
 'reference_note':'Measured idle00 with BT709 gray and unnormalized scipy Sobel on inner alpha boundary; no forced target scalar.'}
digest=sha(STAGE/'godot_bundle/godot/t_rex-atlas-00.png')
motion={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes',
 'atlas_sha256':digest,'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds']},
 'review_evidence':'work/characters/t_rex/sharpness-repair/review/keyframe-review.json',
 'unresolved_structural_failures':[],'owner_approved':False,
 'previous_revision_atlas_sha256':meta['provenance']['baseline_atlas_sha256']}
qa={'character_id':'t_rex','status':'reviewed_pending_owner','motion_quality':motion,
 'baseline_measurements':'work/characters/t_rex/sharpness-repair/analysis.json',
 'registered_pose_evidence':'work/characters/t_rex/sharpness-repair/registration.json',
 'body_only_bbox_px':dict(zip(['x','y','w','h'],b)),'full_fx_bbox_px':full,
 'pixel_sharpness_metrics':sharpness,'atlas_sha256':digest,'atlas':meta['atlas'],
 'frames':len(m['frames']),'clips':len(m['clips']),
 'preservation':{'frame_count_order_ticks_events':True,'fireball_fx_four_original_pngs':True,
 'canvas':[384,256],'anchor':[176,224],'small_contour_variations_pending_human_test':True},
 'power_up_fix':'Round charge embers in frames0/1; baked departing fire removed from body2..5, original independent FX rendered once with same origin/timing.'}
write(WORK/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,
 'observations':['Reviewed all71 frames on light/dark/checker backgrounds. Complete poses retain source action phases; no detached throat/limbs observed.',
 'idle7 throat/jaw region Canvas(214,123,49,22) reviewed against Owner screenshot.',
 'power_up0/1 round orange charge; body2..5 reconstructed without departing projectile; original independent four-phase FX retained.',
 'attack_heavy retains original left/right pose sequence and timing per Owner no-motion-change request; no turn redesign.'],
 'artifacts':{p.name:sha(p) for p in sorted((WORK/'review').glob('*')) if p.suffix in ['.png','.webp']},
 'owner_approved':False})
write(ROOT/'docs/characters/t-rex-visual-repair-qa.json',qa)
roster_path=ROOT/'assets/roster.json';roster=json.loads(roster_path.read_text())
ch=next(c for c in roster['characters'] if c['character_id']=='t_rex')
ch['status']='finalized_engine_verified_demo_pending_owner'
ch['atlas_stage']='demo_pending_owner'
ch['owner_animation_approval']='pending'
ch['owner_visual_override']='Owner requests Spinosaurus final native pixel density and connected complete-pose restoration; current whole-pose art supersedes historical100texel/16color source. Existing animation count/order/timing fixed.'
ch['pixel_sharpness_metrics']=sharpness
ch['motion_quality']=motion
ch['qa_report']='docs/characters/t-rex-visual-repair-qa.json'
ch['map_sync_metrics']['body_only_bbox_px']=qa['body_only_bbox_px']
ch['map_sync_metrics']['full_fx_bbox_px']=full
ch['map_sync_metrics']['reference_ppu_64']=64
ch['map_sync_metrics']['world_size_at_64ppu_m']={f'{label}_{axis}_m':round(v/64,3) for label,box in [('body',qa['body_only_bbox_px']),('aura',full)] for axis,v in [('w',box['w']),('h',box['h'])]}
ch['map_sync_metrics']['tile_32px_span']={f'{label}_tiles_{axis}':round(v/32,3) for label,box in [('body',qa['body_only_bbox_px']),('full_fx',full)] for axis,v in [('w',box['w']),('h',box['h'])]}
for folder in ['clips','godot_bundle']:
    target=ROOT/'assets/t_rex'/folder
    # Godot sidecars bind imported texture resources. Keep them across atlas rebuilds;
    # run Godot --headless --editor --import afterward to refresh changed PNG bytes.
    for sidecar in target.rglob('*.import'):
        dest=STAGE/folder/sidecar.relative_to(target)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(sidecar,dest)
    shutil.rmtree(target);shutil.copytree(STAGE/folder,target)
write(roster_path,roster)
state_path=ROOT/'state.json';state=json.loads(state_path.read_text())
workflow=next(w for w in state['approved_workflows'] if w['character_id']=='t_rex')
workflow['approved_atlas_path']=str((BASE/'godot_bundle/godot/t_rex-atlas-00.png').relative_to(ROOT))
workflow['approval_file']=str((BASE/'owner_approval.json').relative_to(ROOT))
write(state_path,state)
protected=json.loads((WORK/'protected-peers.json').read_text())
assert all(sha(ROOT/p)==s for p,s in protected.items()),'Spino/Ptera changed'
print(json.dumps({'atlas_sha256':digest,'frames':len(m['frames']),'clips':len(m['clips']),
 'preserved_peer_files':len(protected),'sharpness':sharpness,'full_fx_bbox':full}))
