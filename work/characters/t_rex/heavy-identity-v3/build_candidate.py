#!/usr/bin/env python3
"""Preserve approved spin phases; restore canonical identity as complete poses."""
import importlib.util
import hashlib
import json
from pathlib import Path

from PIL import Image

WORK=Path(__file__).resolve().parent
STAGE=WORK/'stage'
BASE=WORK/'baseline'
ROOT=WORK.parents[3]
TICKS=[5,4,2,1,1,1,1,2,3,4,5,6]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def main():
    spec=importlib.util.spec_from_file_location('whole_pose_builder',WORK.parent/'heavy-spin-v2/build_candidate.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    builder.WORK=WORK;builder.STAGE=STAGE;builder.BASE=BASE
    builder.main()
    baseline=json.loads((BASE/'clips/animation-clips.json').read_text())
    old=baseline['clips']['attack_heavy']
    # Whole canonical ready pose reused for both ends of this ONESHOT, not limbs.
    canonical=Image.open(WORK/'canonical-idle-00.png').convert('RGBA')
    dy=225-(canonical.getbbox()[3]-1)
    ready=Image.new('RGBA',(384,256));ready.alpha_composite(canonical,(0,dy))
    for i in [0,11]:ready.save(STAGE/'raw_frames'/f'attack_heavy_{i:02d}.png')
    ev=json.loads((WORK/'frame-evidence.json').read_text())
    ev['identity_reference']={'file':'canonical-idle-00.png','sha256':builder.sha(WORK/'canonical-idle-00.png'),
        'owner_reference':'image copy 5.png','motion_accepted_from_atlas':'7cdc28601c3f8ac7867409d4bd6c036e78c5091ffd3d45751a7db1f12798d7e7'}
    ev['motion_reference']={'character':'t_rex','clip':'attack_heavy','accepted_by_owner':True,
        'scope':'Tail-spin phase order/ticks/events, not prior character appearance'}
    for i in [0,11]:
        ev['phases'][i].update(source='canonical-idle-00.png',complete_body_generated=False,
            reused_complete_canonical_pose=True,whole_frame_translation_px=[0,dy],
            sha256=builder.sha(STAGE/'raw_frames'/f'attack_heavy_{i:02d}.png'))
    source=json.loads((STAGE/'clips_manifest.json').read_text())
    assert source['clips']['attack_heavy']==json.loads((BASE/'clips/source-manifest.json').read_text())['clips']['attack_heavy']
    builder.write(WORK/'frame-evidence.json',ev)
    spec=importlib.util.spec_from_file_location('review',WORK.parent/'sharpness-repair/restore_frames.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.WORK=WORK
    images=[Image.open(STAGE/'raw_frames'/f'attack_heavy_{i:02d}.png').convert('RGBA') for i in range(12)]
    mod.review('attack_heavy',images,old['ticks'])
    guide=Image.new('RGBA',(1536,1024))
    for i,im in enumerate(images):guide.alpha_composite(im,(i%4*384,i//4*320+42))
    guide.save(WORK/'canonical-anchored-edit-target.png')
    print('Motion manifest unchanged; ready0/11 reuse whole canonical pose; no part compositing.')

if __name__=='__main__':main()
