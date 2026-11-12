"""Register complete generated poses; never compose anatomical fragments."""
import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

WORK = Path(__file__).resolve().parent
BASE = WORK / 'baseline'
STAGE = WORK / 'stage'
ROOT = WORK.parents[3]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    previous = json.loads((BASE/'clips/animation-clips.json').read_text())
    source = json.loads((BASE/'clips/source-manifest.json').read_text())
    (STAGE/'raw_frames').mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('review', WORK.parent/'sharpness-repair/restore_frames.py')
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    review.WORK = WORK
    evidence = []
    for name, clip in previous['clips'].items():
        images = []
        sheet = None
        if name != 'fireball_fx':
            sheet = Image.open(WORK/'generated'/f'{name}.png').convert('RGBA')
            assert sheet.size == (1536,1024), (name,sheet.size)
            assert np.array(sheet)[:,:,3].min() == 0, (name,'background must be transparent')
        for i, idx in enumerate(clip['frames']):
            rec = previous['frames'][idx]
            original = Image.open(BASE/'clips'/rec['file']).convert('RGBA')
            dest = STAGE/'raw_frames'/f'{name}_{i:02d}.png'
            if name == 'fireball_fx' or (name == 'walk' and i == 0):
                shutil.copyfile(BASE/'clips'/rec['file'], dest)
                im = original
                entry = {'clip':name,'position':i,'preserved_exact_png':True}
            else:
                x,y = i%4*384, i//4*320
                tile = sheet.crop((x,y,x+384,y+320))
                a = np.array(tile)
                a[:,:,3] = np.where(a[:,:,3]>=128,255,0)
                a[a[:,:,3]==0] = 0
                tile = Image.fromarray(a)
                bbox = tile.getbbox()
                assert bbox and 0 < bbox[0] < bbox[2] < 384 and 0 < bbox[1] < bbox[3] < 320, (name,i,bbox)
                ob = original.getbbox()
                if name == 'attack_heavy':
                    # One uniform scale across all views, never per-angle bbox fitting.
                    tile = tile.resize((242,202), Image.Resampling.NEAREST)
                    nb = tile.getbbox()
                    offset = [176-round(192*242/384),225-(nb[3]-1)]
                else:
                    # Preserve original locomotion/contact trajectory. No pose resizing.
                    offset = [ob[0]-bbox[0],ob[3]-bbox[3]]
                im = Image.new('RGBA',(384,256))
                im.alpha_composite(tile,tuple(offset))
                im.save(dest)
                entry = {'clip':name,'position':i,'source_cell':[x,y,384,320],
                         'source_bbox':list(bbox),'whole_frame_offset':offset,
                         'uniform_scale':242/384 if name=='attack_heavy' else 1,
                         'body_part_transforms':False}
            entry.update(sha256=sha(dest),canvas_bbox=list(im.getbbox()))
            evidence.append(entry)
            images.append(im)
        review.review(name,images,clip['ticks'])
    # Preserve frame names/order and all timing/event/state data from the baseline.
    for frame in source['frames']:
        frame['file']='raw_frames/'+frame['name']+'.png'
    write(STAGE/'clips_manifest.json',source)
    write(WORK/'registration.json',evidence)
    assert sha(STAGE/'raw_frames/walk_00.png') == sha(WORK/'walk-00-reference.png')
    protected=json.loads((WORK/'protected-peers.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    print(json.dumps({'frames':len(evidence),'protected_peer_files':len(protected),
                      'reference_sha256':sha(WORK/'walk-00-reference.png')}))

if __name__=='__main__':
    main()
