#!/usr/bin/env python3
"""Register complete imagegen poses to their original full-frame envelopes.

Only whole-frame crop/Nearest registration and alpha cleanup are performed.
No anatomical pieces are cut, warped, painted, or composited.
"""
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

WORK = Path(__file__).resolve().parent
BASE = WORK / 'baseline/assets/t_rex'
STAGE = WORK / 'stage'

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def metrics(image):
    a = np.array(image)
    mask = a[:, :, 3] > 0
    gray = a[:, :, :3].astype(float) @ np.array([.2126, .7152, .0722])
    edge = mask & ~ndimage.binary_erosion(mask)
    sobel = np.hypot(ndimage.sobel(gray, axis=0), ndimage.sobel(gray, axis=1))
    b = image.getbbox()
    return {'bbox_px': [b[0], b[1], b[2]-b[0], b[3]-b[1]],
            'edge_acutance_sobel': float(sobel[edge].mean()),
            'visible_pixels': int(mask.sum()),
            'rgb_colors': int(len(np.unique(a[mask, :3], axis=0))),
            'alpha_hardness_pct': 100 * float(np.isin(a[:, :, 3], [0, 255]).mean())}

def review(name, images, ticks):
    out = WORK / 'review'
    out.mkdir(exist_ok=True)
    cols = min(5, len(images)); rows = math.ceil(len(images)/cols)
    boxes = [im.getbbox() for im in images]
    box = (min(b[0] for b in boxes)-4, min(b[1] for b in boxes)-4,
           max(b[2] for b in boxes)+4, max(b[3] for b in boxes)+4)
    w, h = box[2]-box[0], box[3]-box[1]
    sheet = Image.new('RGBA', (cols*(2*w+4), 3*(rows*(2*h+20)+24)), '#343a46')
    d = ImageDraw.Draw(sheet)
    for k, bg in enumerate(['light', 'dark', 'checker']):
        top = k*(rows*(2*h+20)+24)
        d.text((4, top+4), f'{name} / {bg} / ORIGINAL TIMING', fill='white')
        for i, im in enumerate(images):
            tile = Image.new('RGBA', (w,h), '#f5f5f5' if bg=='light' else '#171b23')
            if bg=='checker':
                td=ImageDraw.Draw(tile)
                for y in range(0,h,8):
                    for x in range(0,w,8):
                        td.rectangle((x,y,x+7,y+7), fill='#aaaaaa' if (x//8+y//8)%2 else '#dddddd')
            tile.alpha_composite(im.crop(box))
            x=i%cols*(2*w+4); y=top+24+i//cols*(2*h+20)
            sheet.alpha_composite(tile.resize((2*w,2*h), Image.Resampling.NEAREST),(x,y))
            d.text((x,y+2*h), f'{i}: {ticks[i]} ticks', fill='white')
    sheet.save(out/f'filmstrip-{name}.png')
    pics=[]
    for im in images:
        bg=Image.new('RGBA',im.size,'#eeeeea'); bg.alpha_composite(im)
        pics.append(bg.resize((768,512),Image.Resampling.NEAREST))
    pics[0].save(out/f'playback-{name}.webp', save_all=True, append_images=pics[1:],
                 duration=[round(t*1000/60) for t in ticks], loop=0, lossless=True)

def main():
    m=json.loads((BASE/'clips/animation-clips.json').read_text())
    source=json.loads((BASE/'clips/source-manifest.json').read_text())
    (STAGE/'raw_frames').mkdir(parents=True,exist_ok=True)
    evidence=[]
    for name, clip in m['clips'].items():
        sheet = None if name=='fireball_fx' else Image.open(WORK/'generated'/f'{name}.png').convert('RGBA')
        if sheet: assert sheet.size==(1536,1024), (name,sheet.size)
        images=[]
        for i, idx in enumerate(clip['frames']):
            record=m['frames'][idx]
            old=Image.open(BASE/'clips'/record['file']).convert('RGBA')
            dest=STAGE/'raw_frames'/f'{name}_{i:02d}.png'
            if sheet is None:
                shutil.copyfile(BASE/'clips'/record['file'], dest)
                im=old
            else:
                x=i%4*384; y=i//4*341+42
                tile=sheet.crop((x,y,x+384,y+256))
                a=np.array(tile)
                a[:,:,3]=np.where(a[:,:,3]>=128,255,0)
                a[a[:,:,3]==0]=0
                tile=Image.fromarray(a)
                nb=tile.getbbox(); ob=old.getbbox()
                if name=='power_up' and 2<=i<=5:
                    # Historical body PNGs baked the SAME independently rendered FX.
                    # Remove the known FX ownership mask only to measure body bounds;
                    # imagegen restores the complete body, never a patched body fragment.
                    fxidx=m['clips']['fireball_fx']['frames'][i-2]
                    fx=Image.open(BASE/'clips'/m['frames'][fxidx]['file']).convert('RGBA')
                    ownership=Image.new('RGBA',(384,256))
                    ownership.alpha_composite(fx,(304-176,138-128))
                    old_body=np.array(old); old_body[np.array(ownership)[:,:,3]>0]=0
                    ob=Image.fromarray(old_body).getbbox()
                assert nb and ob, (name,i,'missing pose')
                # Whole-pose registration; the original full envelope/ground stays fixed.
                registered=tile.crop(nb).resize((ob[2]-ob[0],ob[3]-ob[1]),Image.Resampling.NEAREST)
                im=Image.new('RGBA',(384,256))
                im.alpha_composite(registered,ob[:2]); im.save(dest)
                evidence.append({'clip':name,'position':i,'original_bbox':list(ob),
                    'generated_bbox_in_cell':list(nb),'registered_bbox':list(im.getbbox()),
                    'processing':'complete pose only; alpha128 threshold, one Nearest registration',
                    'source_sheet_sha256':sha(WORK/'generated'/f'{name}.png'),
                    'frame_sha256':sha(dest)})
            images.append(im)
        review(name,images,clip['ticks'])
    write(STAGE/'clips_manifest.json',source)
    write(WORK/'registration.json',evidence)
    idle=Image.open(STAGE/'raw_frames/idle_00.png').convert('RGBA')
    write(WORK/'candidate-metrics.json',metrics(idle))
    print(json.dumps({'frames':len(source['frames']),'clips':len(source['clips']),
                      'restored_body_frames':len(evidence),'idle':metrics(idle)}))

if __name__=='__main__': main()
