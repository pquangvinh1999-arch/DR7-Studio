#!/usr/bin/env python3
"""Install only the reviewed heavy revision; record pending Owner acceptance."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from build_candidate import WORK,BASE,STAGE,ROOT,write,sha,TICKS

path=STAGE/'godot_bundle/engine-export.json';meta=json.loads(path.read_text())
old=json.loads((BASE/'godot_bundle/engine-export.json').read_text())
meta['source']['path']='../clips/animation-clips.json'
meta['render_contract']=copy.deepcopy(old['render_contract'])
meta['provenance']=copy.deepcopy(old.get('provenance',{}))
meta['provenance'].update(motion='imagegen_complete_body_keyframes',
    attack_heavy_source='work/characters/t_rex/heavy-spin-v2/sheet.png',
    attack_heavy_processing='12 complete perspective poses, fixed whole-cell Nearest scale and common hip/ground registration; no flip/part-warp motion',
    prior_demo_atlas_sha256=sha(BASE/'godot_bundle/godot/t_rex-atlas-00.png'),
    owner_animation_approved=False,atlas_demo_only=True)
meta['provenance']['animation_constraint']='Only attack_heavy redesigned; all61 nonheavy PNGs and their clip timing/events preserved.'
write(path,meta);(STAGE/'clips/.gdignore').touch()
current=json.loads((STAGE/'clips/animation-clips.json').read_text())
previous=json.loads((BASE/'clips/animation-clips.json').read_text())
preserved=[]
for name,clip in current['clips'].items():
    if name=='attack_heavy':continue
    for key in ['ticks','duration_ms','loop','loop_policy','events_ms']:
        assert clip.get(key)==previous['clips'][name].get(key),(name,key)
    for newidx,oldidx in zip(clip['frames'],previous['clips'][name]['frames']):
        a=STAGE/'clips'/current['frames'][newidx]['file'];b=BASE/'clips'/previous['frames'][oldidx]['file']
        assert sha(a)==sha(b),(name,newidx,oldidx)
        preserved.append({'clip':name,'source_frame_name':previous['frames'][oldidx]['name'],'sha256':sha(a)})
assert len(preserved)==61
assert current['clips']['attack_heavy']['ticks']==TICKS
assert len(current['frames'])==73
digest=sha(STAGE/'godot_bundle/godot/t_rex-atlas-00.png')
roster_path=ROOT/'assets/roster.json';roster=json.loads(roster_path.read_text())
char=next(c for c in roster['characters'] if c['character_id']=='t_rex')
motion=copy.deepcopy(char['motion_quality'])
motion.update(status='reviewed_pending_owner',method='imagegen_complete_body_keyframes',
    atlas_sha256=digest,review_evidence='work/characters/t_rex/heavy-spin-v2/review/keyframe-review.json',
    unresolved_structural_failures=[],owner_approved=False,
    prior_demo_atlas_sha256=sha(BASE/'godot_bundle/godot/t_rex-atlas-00.png'))
motion['checks']={k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds']}
char['motion_quality']=motion;char['atlas_stage']='demo_pending_owner'
char['status']='finalized_engine_verified_demo_pending_owner'
char['owner_animation_approval']='pending'
char['qa_report']='docs/characters/t-rex-heavy-spin-v2-qa.json'
char['facing_contract']['locomotion_vector_rule']='Bipedal two-hind-leg walk/run unchanged; attack_heavy uses complete front/three-quarter/rear poses for a360degree planted tail whip toward screen+X.'
# Recompute full gameplay envelope including the unchanged independent projectile.
union=np.zeros((256,384),bool)
frames={n:[Image.open(STAGE/'clips'/current['frames'][idx]['file']).convert('RGBA') for idx in c['frames']] for n,c in current['clips'].items()}
for images in frames.values():
    for im in images:union|=np.array(im)[:,:,3]>0
for i in range(4):
    im=frames['power_up'][i+2].copy();im.alpha_composite(frames['fireball_fx'][i],(128,10));union|=np.array(im)[:,:,3]>0
y,x=np.where(union);full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
char['map_sync_metrics']['full_fx_bbox_px']=full
char['map_sync_metrics']['world_size_at_64ppu_m'].update(aura_w_m=round(full['w']/64,3),aura_h_m=round(full['h']/64,3))
char['map_sync_metrics']['tile_32px_span'].update(full_fx_tiles_w=round(full['w']/32,3),full_fx_tiles_h=round(full['h']/32,3))
qa={'character_id':'t_rex','status':'reviewed_pending_owner','scope':'attack_heavy only',
    'atlas_sha256':digest,'atlas':meta['atlas'],'frames':73,'clips':9,
    'motion_quality':motion,'source_evidence':'work/characters/t_rex/heavy-spin-v2/frame-evidence.json',
    'owner_report':'Prior heavy changes right-side frame1 directly to left-side frame2; looks like flat-image flip.',
    'fix':'12 complete poses include true front4/back7 and transitional angles; common pivot and ground; fast strike5, small amber tail-tipVFX5, fading6, dissipated7.',
    'heavy_ticks':TICKS,'heavy_total_ticks':sum(TICKS),'heavy_duration_ms':sum(TICKS)*1000/60,
    'hit_frame':5,'hit_at_tick':sum(TICKS[:5]),'active_end_frame':7,
    'preserved_nonheavy_pngs':preserved,'preserved_nonheavy_count':len(preserved),
    'body_only_bbox_px':char['map_sync_metrics']['body_only_bbox_px'],'full_fx_bbox_px':full,
    'pixel_sharpness_metrics':char['pixel_sharpness_metrics'],
    'sharpness_standard':'docs/art-standards/character-pixel-sharpness.json',
    'owner_animation_approved':False}
write(ROOT/'docs/characters/t-rex-heavy-spin-v2-qa.json',qa)
write(WORK/'review/keyframe-review.json',{'status':'reviewed_pending_owner','atlas_sha256':digest,
    'scope':'12 new heavy poses plus entry/return poses; all61 other frames unchanged',
    'observations':['Whole-body pose4 faces camera with chest/belly; pose7 shows back of skull/neck/hips, no copied front face.',
        'Frames2/3/6/8 have differing chest/back/limb occlusion and tail foreshortening; true views rather than horizontal flips.',
        'All12 complete poses reviewed on light/dark/checker. Ground225 and pelvis reference176 remain common; natural perspective widths retained.',
        'Ticks5/4 anticipation then2/1/1/1/1/2 accelerated turn/impact, recovery3/4/5/6; tiny amber slash5, fading6, dissipated7.',
        'Naturalness/feel remains pending Owner Human Test.'],
    'artifacts':{p.name:sha(p) for p in sorted((WORK/'review').glob('*')) if p.suffix in ['.png','.webp']},
    'owner_approved':False})
for folder in ['clips','godot_bundle']:
    target=ROOT/'assets/t_rex'/folder
    for sidecar in target.rglob('*.import'):
        dest=STAGE/folder/sidecar.relative_to(target);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sidecar,dest)
    shutil.rmtree(target);shutil.copytree(STAGE/folder,target)
write(roster_path,roster)
protected=json.loads((WORK/'protected-peers.json').read_text())
assert all(sha(ROOT/p)==h for p,h in protected.items()),'Spino/Ptera changed'
print(json.dumps({'atlas_sha256':digest,'frames':73,'heavy_frames':12,'heavy_ticks':35,
    'preserved_other_frames':len(preserved),'protected_peer_files':len(protected),'full_fx_bbox_px':full}))
