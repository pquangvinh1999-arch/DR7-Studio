#!/usr/bin/env python3
"""Replace only heavy with complete perspective poses; keep all other PNGs/timing."""
import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

WORK=Path(__file__).resolve().parent
BASE=WORK/'baseline'
STAGE=WORK/'stage'
ROOT=WORK.parents[3]
TICKS=[5,4,2,1,1,1,1,2,3,4,5,6]
PHASES=['ready_right','windup_coil_right','turn_toward_camera_20deg',
        'front_three_quarter_50deg','true_front_90deg','tail_strike_left_side_180deg',
        'rear_left_three_quarter_220deg','true_back_270deg',
        'rear_right_three_quarter_310deg','decelerate_right_340deg',
        'recover_right','ready_right']

def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=json.loads((BASE/'clips/source-manifest.json').read_text())
    previous=json.loads((BASE/'clips/animation-clips.json').read_text())
    sheet=Image.open(WORK/'sheet.png').convert('RGBA')
    assert sheet.size==(1536,1024),sheet.size
    layout=json.loads((WORK/'sheet-layout.json').read_text()) if (WORK/'sheet-layout.json').exists() else {'scaled_cell_px':[256,213],'hip_source_x':192}
    (STAGE/'raw_frames').mkdir(parents=True,exist_ok=True)
    frames=[];evidence=[]
    reference=Image.open(BASE/'clips'/previous['frames'][previous['clips']['attack_heavy']['frames'][0]]['file']).convert('RGBA')
    ground=reference.getbbox()[3]-1
    for i in range(12):
        # Observed source row content repeats at320px with64px empty bottom.
        # Every complete pose is wholly inside its cell; do not assume341px gutters.
        x=i%4*384;y=i//4*320
        tile=sheet.crop((x,y,x+384,y+320))
        a=np.array(tile);a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
        tile=Image.fromarray(a)
        labels,count=ndimage.label(a[:,:,3]>0)
        assert count,(i,'missing body')
        areas=np.bincount(labels.ravel());areas[0]=0;body=labels==areas.argmax()
        by,bx=np.where(body)
        assert bx.min()>0 and bx.max()<383 and by.min()>0 and by.max()<319,(i,'clipped complete pose')
        # Fixed uniform scale and horizontal pelvis axis for every angle.
        # Never expand a front/back silhouette to the side-view width.
        target_size=tuple(layout['scaled_cell_px'])
        scaled=tile.copy() if target_size==tile.size else tile.resize(target_size,Image.Resampling.NEAREST)
        la=np.array(scaled);sl,sc=ndimage.label(la[:,:,3]>0)
        areas=np.bincount(sl.ravel());areas[0]=0;sy,sx=np.where(sl==areas.argmax())
        offset=[int(round(176-layout['hip_source_x']*target_size[0]/384)),int(ground-sy.max())]
        im=Image.new('RGBA',(384,256));im.alpha_composite(scaled,tuple(offset))
        out=STAGE/'raw_frames'/f'attack_heavy_{i:02d}.png';im.save(out)
        frames.append({'name':f'attack_heavy_{i:02d}','file':f'raw_frames/attack_heavy_{i:02d}.png'})
        evidence.append({'index':i,'phase':PHASES[i],'ticks':TICKS[i],
            'sheet_cell_px':[x,y,384,320],
            'source_body_bbox_px':[int(bx.min()),int(by.min()),int(bx.max()-bx.min()+1),int(by.max()-by.min()+1)],
            'source_foot_span_x':[int(bx[by>=by.max()-2].min()),int(bx[by>=by.max()-2].max())],
            'body_ground_canvas_y':ground,'whole_cell_scale_from':[384,320],'whole_cell_scale_to':list(target_size),
            'whole_cell_offset_px':offset,'canvas_bbox_px':list(im.getbbox()),
            'complete_body_generated':True,'body_part_warping':False,'sha256':sha(out)})
    clip=copy.deepcopy(source['clips']['attack_heavy'])
    clip.update(frames=[f['name'] for f in frames],ticks=TICKS,
        keys={'wind_start':0,'wind_peak':1,'strike':5,'recover':8,'end':11},
        events=[{'at':1,'name':'tell'},{'at':5,'name':'hit'},{'at':7,'name':'active_end'},{'at':11,'name':'end'}])
    source['clips']['attack_heavy']=clip
    allframes=[];preserved=[]
    for n,c in source['clips'].items():
        if n=='attack_heavy':allframes.extend(frames);continue
        oldclip=previous['clips'][n]
        for name,index in zip(c['frames'],oldclip['frames']):
            src=BASE/'clips'/previous['frames'][index]['file'];dest=STAGE/'raw_frames'/f'{name}.png'
            shutil.copyfile(src,dest);assert sha(src)==sha(dest)
            allframes.append({'name':name,'file':f'raw_frames/{name}.png'})
            preserved.append({'name':name,'sha256':sha(dest)})
    source['frames']=allframes
    write(STAGE/'clips_manifest.json',source)
    write(WORK/'frame-evidence.json',{'source_sha256':sha(WORK/'sheet.png'),
        'ground_canvas_y':ground,'horizontal_pivot_canvas_x':176,
        'phases':evidence,'preserved_nonheavy_frames':preserved,
        'motion_reference':{'character':'spinosaurus','clip':'attack_heavy','reference_ticks':TICKS,
          'use':'Perspective, occlusion, anticipation/fast impact/recovery only; no Spino sprite pixels copied'},
        'heavy_previous_ticks':previous['clips']['attack_heavy']['ticks'],
        'heavy_new_ticks':TICKS,'total_ticks':sum(TICKS),'owner_review':'pending'})
    spec=importlib.util.spec_from_file_location('review_tools',WORK.parent/'sharpness-repair/restore_frames.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.WORK=WORK
    module.review('attack_heavy',[Image.open(STAGE/f['file']).convert('RGBA') for f in frames],TICKS)
    print(json.dumps({'total_frames':len(allframes),'heavy_frames':12,'ticks':sum(TICKS),'ground_y':ground,'preserved_frames':len(preserved)}))

if __name__=='__main__':main()
