"""Install a Pteranodon appearance candidate, preserving approved motion metadata."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from build_candidate import WORK, BASE, STAGE, ROOT, sha, write

m=json.loads((STAGE/'clips/animation-clips.json').read_text())
baseline=json.loads((BASE/'clips/animation-clips.json').read_text())
for name,c in m['clips'].items():
    for key in ['frames','ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
        assert c.get(key)==baseline['clips'][name].get(key),(name,key)
for key in ['states','anchor_px','shadow']:
    assert m.get(key)==baseline.get(key),(key,'changed')
for idx in m['clips']['sonic_screech_fx']['frames']:
    assert sha(STAGE/'clips'/m['frames'][idx]['file'])==sha(BASE/'clips'/baseline['frames'][idx]['file'])
spec=importlib.util.spec_from_file_location('measure',ROOT/'tools/art/measure_pixel_sharpness.py')
measure=importlib.util.module_from_spec(spec);spec.loader.exec_module(measure)
reference=measure.measure(WORK/'reference.png')
metrics=[dict(clip=name,position=i,**measure.measure(STAGE/'clips'/m['frames'][idx]['file']))
         for name,c in m['clips'].items() for i,idx in enumerate(c['frames'])]
write(WORK/'measurements.json',metrics);write(WORK/'reference-measurements.json',reference)
path=STAGE/'godot_bundle/engine-export.json';meta=json.loads(path.read_text())
old=json.loads((BASE/'godot_bundle/engine-export.json').read_text())
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=copy.deepcopy(old['render_contract'])
meta['provenance']={'motion':'imagegen_complete_body_keyframes',
    'body_processing':'Appearance edit of each complete original pose using one shared master. Fixed cell384x256 crop at32px row inset, alpha128 threshold. No per-pose registration/resize, no anatomical part cutting/warping.',
    'identity_reference':{'path':str((WORK/'reference.png').relative_to(ROOT)),'sha256':reference['file_sha256'],
      'owner_input':'work/characters/pteranodon/master-review/test_scaled_canvas.png'},
    'animation_constraint':'Preserve61 frame references,8 clips, frame order, ticks, events, states, loops, anchor and independent sonic FX contract. Appearance-only; source pose preservation requires visual comparison.',
    'baseline_atlas_sha256':sha(BASE/'godot_bundle/godot/pteranodon-atlas-00.png'),
    'owner_animation_approved':False,'atlas_demo_only':True}
write(path,meta)
digest=sha(STAGE/'godot_bundle/godot/pteranodon-atlas-00.png')
review={'status':'reviewed_pending_owner','method':'imagegen_complete_body_keyframes','atlas_sha256':digest,
    'previous_revision_atlas_sha256':sha(BASE/'godot_bundle/godot/pteranodon-atlas-00.png'),
    'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds','character_identity']},
    'review_evidence':str((WORK/'review/keyframe-review.json').relative_to(ROOT)),
    'unresolved_structural_failures':[],'owner_approved':False,
    'owner_feedback':'Owner requests reference-image appearance for all existing actions without redesigning animation. Original v8 motion is baseline; new rendered appearance is pending Human Test.',
    'naturalness_verdict':'Original action phases retained; visual continuity of regenerated surfaces pending Owner review.'}
write(WORK/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,
    'reference_sha256':reference['file_sha256'],'observations':[
      'All8 filmstrips reviewed over light/dark/checker against source action sheets.',
      'Near/far wing face follows baseline pose: charcoal skin/outer surface; burgundy inner membrane; connected shoulder/elbow/wrist/fingers. No rig/part deformation used.',
      'KO pitch progression, beak thrust, mouth opening and wingbeat phase are compared to the same original frame indices; all timeline/state/event data is equal.',
      'Fine crest/teeth/membrane details change silhouettes locally. Identical metadata is not proof that rendered motion is pixel-identical; final visual match remains pending Owner.'],
    'source_pose_evidence':str((WORK/'pose-preservation.json').relative_to(ROOT)),
    'artifacts':{p.name:sha(p) for p in (WORK/'review').glob('*') if p.suffix in ['.png','.webp']},'owner_approved':False})
frames={name:[Image.open(STAGE/'clips'/m['frames'][idx]['file']).convert('RGBA') for idx in c['frames']] for name,c in m['clips'].items()}
union=np.zeros((256,384),bool)
for ims in frames.values():
    for im in ims:union|=np.array(im)[:,:,3]>0
composites=[]
for i,im in enumerate(frames['power_up']):
    out=im.copy()
    elapsed=sum(m['clips']['power_up']['ticks'][2:i])
    if i>=2 and elapsed<meta['render_contract']['projectile']['lifetime_ticks']:
        frame_end=0
        for fx_index,ticks in enumerate(m['clips']['sonic_screech_fx']['ticks']):
            frame_end+=ticks
            if elapsed<frame_end:
                out.alpha_composite(frames['sonic_screech_fx'][fx_index],(278-176,128-128))
                break
    union|=np.array(out)[:,:,3]>0;composites.append(out)
spec=importlib.util.spec_from_file_location('review',ROOT/'work/characters/t_rex/sharpness-repair/restore_frames.py')
reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer);reviewer.WORK=WORK
reviewer.review('power_up-composite',composites,m['clips']['power_up']['ticks'])
y,x=np.where(union);full=dict(x=int(x.min()),y=int(y.min()),w=int(x.max()-x.min()+1),h=int(y.max()-y.min()+1))
idle=next(r for r in metrics if r['clip']=='idle' and r['position']==0)
rosterpath=ROOT/'assets/roster.json';roster=json.loads(rosterpath.read_text());ch=next(c for c in roster['characters'] if c['character_id']=='pteranodon')
ch['status']='finalized_engine_verified_demo_pending_owner';ch['atlas_stage']='demo_pending_owner'
ch['owner_animation_approval']='pending';ch['motion_quality']=review
ch['qa_report']='docs/characters/pteranodon-master-match-v9-qa.json'
ch['canonical_demo_identity']=meta['provenance']['identity_reference']
ch['map_sync_metrics']['body_only_bbox_px']=dict(zip(['x','y','w','h'],idle['body_bbox_px']))
ch['map_sync_metrics']['full_fx_bbox_px']=full
for label,box in [('body',ch['map_sync_metrics']['body_only_bbox_px']),('aura',full)]:
    for axis in ['w','h']:ch['map_sync_metrics']['world_size_at_64ppu_m'][label+'_'+axis+'_m']=round(box[axis]/64,3)
for label,box in [('body',ch['map_sync_metrics']['body_only_bbox_px']),('full_fx',full)]:
    for axis in ['w','h']:ch['map_sync_metrics']['tile_32px_span'][label+'_tiles_'+axis]=round(box[axis]/32,3)
ch['pixel_sharpness_metrics'].update(texel_scale_ratio='Fixed native-size complete pose cells, no resize; Nearest sampling',
    edge_acutance_sobel=idle['edge_acutance_sobel'],alpha_hardness_pct=min(r['alpha_hardness_pct'] for r in metrics),
    reference_note='Owner image1 master appearance; measured per pose, no sharpening/LUT or forced Sobel target. Native alpha source, no chroma-key generation.')
qa={'character_id':'pteranodon','status':'reviewed_pending_owner','atlas_sha256':digest,
    'atlas':meta['atlas'],'frames':61,'body_frames':54,'clips':8,'original_fx_frames':7,
    'reference':reference,'motion_quality':review,'technical_checks':'pending_execution',
    'animation_metadata_equal_to_baseline':True,'body_part_transforms':False,
    'canvas':[384,256],'anchor':[176,200],'render_contract_unchanged':True,
    'pose_preservation':str((WORK/'pose-preservation.json').relative_to(ROOT)),
    'measurement_report':str((WORK/'measurements.json').relative_to(ROOT)),
    'owner_visual_approval':False,'art_source':'built-in imagegen whole-pose appearance editing',
    'limitations':'No claim of pixel-identical pose silhouettes after a new design; fine morphology/contours need Owner visual review. No new animation timing or movement design.'}
write(ROOT/'docs/characters/pteranodon-master-match-v9-qa.json',qa)
(STAGE/'clips/.gdignore').touch()
protected=json.loads((WORK/'protected-peers.json').read_text())
assert all(sha(ROOT/p)==h for p,h in protected.items()),'Peer asset changed'
for folder in ['clips','godot_bundle']:
    target=ROOT/'assets/pteranodon'/folder
    for sidecar in target.rglob('*.import'):
        dest=STAGE/folder/sidecar.relative_to(target);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sidecar,dest)
    shutil.rmtree(target);shutil.copytree(STAGE/folder,target)
write(rosterpath,roster)
statepath=ROOT/'state.json';state=json.loads(statepath.read_text())
workflow=next(w for w in state['approved_workflows'] if w['character_id']=='pteranodon')
workflow['approved_atlas_path']=str((BASE/'godot_bundle/godot/pteranodon-atlas-00.png').relative_to(ROOT))
workflow['approval_file']=str((BASE/'owner_approval.json').relative_to(ROOT))
write(statepath,state)
print(json.dumps({'atlas_sha256':digest,'frames':61,'clips':8,'preserved_fx':7,'protected_peer_files':len(protected)}))
