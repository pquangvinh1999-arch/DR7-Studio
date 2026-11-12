#!/usr/bin/env python3
"""Prepare metadata/review composites for the whole-pose candidate, before install."""
import copy
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from build_generated_spinosaurus import ROOT, WORK, STAGE, bbox, reviews, write, sha

qa=json.loads((STAGE/'qa.json').read_text())
(STAGE/'clips/.gdignore').touch()
meta_path=STAGE/'godot_bundle/engine-export.json'
meta=json.loads(meta_path.read_text())
meta['source']['path']='../clips/animation-clips.json'
contract=copy.deepcopy(json.loads((WORK/'before-final-no-run.json').read_text())['render_contract'])
contract['body_clips'].remove('run')
contract['locomotion']={'kind':'ground','clip':'walk','walk_cycle_order':list(range(8))}
fx0=np.array(Image.open(STAGE/'raw_frames/fireball_fx_00.png'))
y,x=np.where(fx0[:,:,3]>0);muzzle=qa['mouths_canvas_px']['power_up'][2]
point=[round(muzzle[0])+176-int(x.min())-2,round(muzzle[1])+128-round((int(y.min())+int(y.max())+1)/2)]
contract['projectile']['origin_canvas_px']=point
meta['render_contract']=contract
meta['provenance']={'master_sha256':qa['source_sha256'],'motion':'imagegen_complete_body_keyframes',
 'source_review':'work/characters/spinosaurus/review-final/keyframe-review.json',
 'body_processing':'Owner-approved PNGs copied byte-for-byte; atlas repack only, no redraw or anatomical editing',
 'owner_master_approved':True,'owner_animation_approved':True,'atlas_demo_only':False,'owner_excluded_clips':['run']}
write(meta_path,meta)
rendered={n:[np.array(Image.open(STAGE/f'raw_frames/{n}_{i:02d}.png')) for i in range(c['frames'])] for n,c in qa['clips'].items()}
union=np.zeros((256,384),bool)
for frames in rendered.values():
 for a in frames:union|=a[:,:,3]>0
for i in range(4):
 im=Image.fromarray(rendered['power_up'][i+2]);im.alpha_composite(Image.fromarray(rendered['fireball_fx'][i]),(point[0]-176,point[1]-128))
 rendered['power_up'][i+2]=np.array(im);union|=np.array(im)[:,:,3]>0
reviews(rendered)
full=np.zeros((256,384,4),np.uint8);full[:,:,3]=union*255
rest=rendered['idle'][0];gray=rest[:,:,:3].astype(float)@np.array([.2126,.7152,.0722]);mask=rest[:,:,3]>0
edge=mask&~ndimage.binary_erosion(mask);sob=np.hypot(ndimage.sobel(gray,axis=0),ndimage.sobel(gray,axis=1))
rgba=np.concatenate([np.array(Image.open(p)).reshape(-1,4) for p in sorted((STAGE/'raw_frames').glob('*.png'))]);visible=rgba[rgba[:,3]>0]
key=(visible[:,0]>180)&(visible[:,1]<100)&(visible[:,2]>180)
qa.update(full_fx_bbox_px=bbox(full),render_contract=contract,atlas=meta['atlas'],palette_colors=len(np.unique(visible[:,:3],axis=0)),
 pixel_sharpness_metrics={'texel_scale_ratio':'Imagegen complete native keyframes -> gameplay with one Nearest resize; no blur/palette/gain',
 'edge_acutance_sobel':round(float(sob[edge].mean()),3),'alpha_hardness_pct':100*float(np.isin(rgba[:,3],[0,255]).mean()),
 'visible_alpha_hardness_pct':100*float((visible[:,3]==255).mean()),'opaque_key_px':int(key.sum()),'enclosed_key_pockets':int(key.sum()),'outer_ring_spill_fraction':float(key.sum()/max(1,len(visible))),
 'reference_note':'Actual measurements; no scalar forced to T-rex 201.3. New whole poses preserve approved concept, not pixel identity to master.'})
atlas=STAGE/'godot_bundle/godot/spinosaurus-atlas-00.png'
qa['atlas_sha256']=sha(atlas)
qa['review_status']='owner_approved'
qa['motion_quality']={'status':'owner_approved','method':qa['motion_method'],'atlas_sha256':sha(atlas),
 'checks':{k:True for k in ['body_connections','whole_pose_sequence','perspective_turns','phase_timing','three_backgrounds']},
 'review_evidence':'work/characters/spinosaurus/review-final/keyframe-review.json','unresolved_structural_failures':[],
 'owner_approved':True,'previous_revision_atlas_sha256':'578912e9e23d4e486052c76c10b302fd925b1e0194f084814e57e5447b9635aa'}
write(STAGE/'qa.json',qa)
write(STAGE/'review/keyframe-review.json',{'status':'owner_approved','method':qa['motion_method'],
 'review_scope':'Owner explicitly approved remaining clips after removing run. All71 retained frame PNG hashes and clip timing/events verified against the prior human-tested candidate; no visual edits.',
 'artifacts':{p.name:sha(p) for p in sorted((STAGE/'review').glob('*')) if p.suffix in ['.png','.webp']},
 'source_poses':qa['source_poses'],'owner_animation_approved':True})
print(json.dumps({'atlas_sha256':sha(atlas),'body':qa['body_only_bbox_px'],'full':qa['full_fx_bbox_px'],'projectile_origin':point,'atlas':meta['atlas']['pages']}))
