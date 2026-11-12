"""Install the reviewed candidate; preserve historical Owner approval separately."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from build_candidate import WORK, BASE, STAGE, ROOT, sha, write

spec=importlib.util.spec_from_file_location('measure',ROOT/'tools/art/measure_pixel_sharpness.py')
measure=importlib.util.module_from_spec(spec);spec.loader.exec_module(measure)
m=json.loads((STAGE/'clips/animation-clips.json').read_text())
before=json.loads((BASE/'clips/animation-clips.json').read_text())
for name,c in m['clips'].items():
    for key in ['frames','ticks','duration_ms','loop','loop_policy','events_ms','keys','hitstop_ticks']:
        assert c.get(key)==before['clips'][name].get(key),(name,key)
for index in m['clips']['fireball_fx']['frames']+[m['clips']['walk']['frames'][0]]:
    assert sha(STAGE/'clips'/m['frames'][index]['file'])==sha(BASE/'clips'/before['frames'][index]['file'])
measurements=[dict(clip=name,position=i,**measure.measure(STAGE/'clips'/m['frames'][idx]['file']))
              for name,c in m['clips'].items() for i,idx in enumerate(c['frames'])]
write(WORK/'measurements.json',measurements)
reference=measure.measure(WORK/'walk-00-reference.png')
write(WORK/'reference.json',dict(reference,role='Owner selected T-rex walk0; body art style/shading reference, not a new global standard for approved peers'))
meta_path=STAGE/'godot_bundle/engine-export.json'
meta=json.loads(meta_path.read_text())
oldmeta=json.loads((BASE/'godot_bundle/engine-export.json').read_text())
meta['source']['path']='../clips/animation-clips.json'
meta['render_contract']=copy.deepcopy(oldmeta['render_contract'])
meta['provenance']={'motion':'imagegen_complete_body_keyframes',
    'body_processing':'Complete pose style edit, hard alpha threshold128, whole-frame registration. Heavy uses one fixed242/384 nearest scale across all angles. No anatomical cut/warp.',
    'canonical_identity':{'reference':str((WORK/'walk-00-reference.png').relative_to(ROOT)),
        'sha256':reference['file_sha256'],'owner_reference':'T-rex walk frame0',
        'source_roles':'Walk0 alone determines identity, pixel detail and baked shading; other sheets are original pose-layout references.'},
    'owner_animation_approved':False,'atlas_demo_only':True,
    'baseline_atlas_sha256':sha(BASE/'godot_bundle/godot/t_rex-atlas-00.png'),
    'animation_constraint':'73 frames/9 clips; preserve all original tick/event/loop metadata and4 fireball PNGs. Heavy redesigned with crouch, pivot step, tail coil/lag and catch-step instead of upright rigid rotation.'}
write(meta_path,meta)
digest=sha(STAGE/'godot_bundle/godot/t_rex-atlas-00.png')
rosterpath=ROOT/'assets/roster.json';roster=json.loads(rosterpath.read_text())
ch=next(x for x in roster['characters'] if x['character_id']=='t_rex')
review=copy.deepcopy(ch['motion_quality'])
review.update(status='reviewed_pending_owner',method='imagegen_complete_body_keyframes',
    atlas_sha256=digest,owner_approved=False,
    review_evidence='work/characters/t_rex/walk-style-v4/review/keyframe-review.json',
    unresolved_structural_failures=[],
    owner_feedback='Walk0 chosen as style reference; previous rigid turntable heavy rejected. New whole-body crouch/pivot/counterbalance candidate requires new Human Test.',
    owner_accepted_motion=False,identity_owner_approved=False)
review['checks']={k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds','character_identity']}
review['naturalness_verdict']='pending_owner_real_time_review'
ch['motion_quality']=review
ch['canonical_demo_identity']=meta['provenance']['canonical_identity']
ch['atlas_stage']='demo_pending_owner';ch['owner_animation_approval']='pending'
ch['qa_report']='docs/characters/t-rex-walk-style-v4-qa.json'
ch['owner_visual_override']='T-rex walk0 selected 2026-11-12; all body clips style-matched, walk0 PNG preserved; no separate material/gloss shader added.'
frames={name:[Image.open(STAGE/'clips'/m['frames'][idx]['file']).convert('RGBA') for idx in c['frames']] for name,c in m['clips'].items()}
union=np.zeros((256,384),bool)
for ims in frames.values():
    for im in ims:union|=np.array(im)[:,:,3]>0
composites=[]
for i,im in enumerate(frames['power_up']):
    out=im.copy()
    if 2<=i<=5:out.alpha_composite(frames['fireball_fx'][i-2],(128,10))
    union|=np.array(out)[:,:,3]>0;composites.append(out)
spec=importlib.util.spec_from_file_location('review',WORK.parent/'sharpness-repair/restore_frames.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.WORK=WORK
module.review('power_up-composite',composites,m['clips']['power_up']['ticks'])
y,x=np.where(union)
full=dict(x=int(x.min()),y=int(y.min()),w=int(x.max()-x.min()+1),h=int(y.max()-y.min()+1))
idle=next(r for r in measurements if r['clip']=='idle' and r['position']==0)
ch['map_sync_metrics']['body_only_bbox_px']=dict(zip(['x','y','w','h'],idle['body_bbox_px']))
ch['map_sync_metrics']['full_fx_bbox_px']=full
for label,box in [('body',ch['map_sync_metrics']['body_only_bbox_px']),('aura',full)]:
    for axis in ['w','h']:ch['map_sync_metrics']['world_size_at_64ppu_m'][label+'_'+axis+'_m']=round(box[axis]/64,3)
for label,box in [('body',ch['map_sync_metrics']['body_only_bbox_px']),('full_fx',full)]:
    for axis in ['w','h']:ch['map_sync_metrics']['tile_32px_span'][label+'_tiles_'+axis]=round(box[axis]/32,3)
# Keep existing key metrics only after confirming native-alpha inputs and no key pixels;
# the source route here is real alpha, not chroma-key extraction.
allpixels=np.concatenate([np.array(im).reshape(-1,4) for ims in frames.values() for im in ims])
visible=allpixels[allpixels[:,3]>0]
magenta=(visible[:,0]>180)&(visible[:,1]<100)&(visible[:,2]>180)
assert not magenta.any()
ch['pixel_sharpness_metrics'].update(edge_acutance_sobel=idle['edge_acutance_sobel'],
    alpha_hardness_pct=float(np.isin(allpixels[:,3],[0,255]).mean()*100),
    reference_note='Walk0 canonical reference230.524; current idle measured separately. Native alpha source, no target Sobel fitting.')
write(WORK/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,
    'observations':['All9 filmstrips opened over light/dark/checker; walk0 remains exact source PNG.',
      'Heavy0/1→4 lowers center of mass and changes bent-knee contact;5 strikes with torso lowered;6/7 lift trailing foot;8/9 catch-step and tail recovery. See per-frame Canvas bboxes in registration.json.',
      'Body palette, cream jaw/throat, sparse scale highlights matched against walk0; identity/shading final judgment remains with Owner.',
      'Timing and hit events retained; playback WebP available for each action. No subjective naturalness PASS is implied by technical verification.'],
    'naturalness':'pending_owner_real_time_review','owner_approved':False,
    'artifacts':{p.name:sha(p) for p in (WORK/'review').glob('*') if p.suffix in ['.png','.webp']}})
qa={'character_id':'t_rex','status':'reviewed_pending_owner','atlas_sha256':digest,
    'reference':reference,'frames':73,'clips':9,'atlas':meta['atlas'],
    'motion_quality':review,'technical_checks':'pending_execution',
    'motion_naturalness':'pending_owner_real_time_review','measurements':str((WORK/'measurements.json').relative_to(ROOT)),
    'frame_registration':str((WORK/'registration.json').relative_to(ROOT)),
    'preserved':['walk0 exact PNG','4 independent fireball PNGs','all tick/event/loop metadata','500 Spinosaurus/Pteranodon files'],
    'art_source':'built-in imagegen; whole-body keyframe generation/style editing',
    'limits':'Image generation cannot guarantee exact pose/identity preservation; review candidate against locked walk0. No automatic aesthetic score or GPU/mobile claim.'}
write(ROOT/'docs/characters/t-rex-walk-style-v4-qa.json',qa)
(STAGE/'clips/.gdignore').touch()
protected=json.loads((WORK/'protected-peers.json').read_text())
assert all(sha(ROOT/p)==h for p,h in protected.items())
for folder in ['clips','godot_bundle']:
    target=ROOT/'assets/t_rex'/folder
    for sidecar in target.rglob('*.import'):
        dest=STAGE/folder/sidecar.relative_to(target);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sidecar,dest)
    shutil.rmtree(target);shutil.copytree(STAGE/folder,target)
write(rosterpath,roster)
print(json.dumps({'atlas_sha256':digest,'reference_sha256':reference['file_sha256'],'frames':73,'clips':9,'protected_peer_files':len(protected),'motion_naturalness':'pending_owner'}))
