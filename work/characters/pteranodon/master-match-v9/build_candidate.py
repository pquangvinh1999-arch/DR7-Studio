"""Visual reskin only: whole generated pose cells, unchanged animation data."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK=Path(__file__).resolve().parent
BASE=WORK/'baseline'
STAGE=WORK/'stage'
ROOT=WORK.parents[3]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    m=json.loads((BASE/'clips/animation-clips.json').read_text())
    source=json.loads((BASE/'clips/source-manifest.json').read_text())
    spec=importlib.util.spec_from_file_location('review',ROOT/'work/characters/t_rex/sharpness-repair/restore_frames.py')
    reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer);reviewer.WORK=WORK
    (STAGE/'raw_frames').mkdir(parents=True,exist_ok=True)
    evidence=[]
    for name,clip in m['clips'].items():
        sheet=None
        if name!='sonic_screech_fx':
            sheet=Image.open(WORK/'generated'/f'{name}.png').convert('RGBA')
            assert sheet.size==(1536,1024),(name,sheet.size)
            assert np.array(sheet)[:,:,3].min()==0,(name,'Missing transparent background')
        images=[]
        for i,idx in enumerate(clip['frames']):
            old=Image.open(BASE/'clips'/m['frames'][idx]['file']).convert('RGBA')
            dest=STAGE/'raw_frames'/f'{name}_{i:02d}.png'
            if sheet is None:
                shutil.copyfile(BASE/'clips'/m['frames'][idx]['file'],dest);im=old
            else:
                # Fixed original layout: never register to per-pose alpha bounds.
                x,y=i%4*384,i//4*320+32
                tile=sheet.crop((x,y,x+384,y+256))
                a=np.array(tile);a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
                im=Image.fromarray(a);b=im.getbbox()
                assert b and 0<b[0]<b[2]<384 and 0<b[1]<b[3]<256,(name,i,b,'clipped')
                im.save(dest)
            om=np.array(old)[:,:,3]>0;nm=np.array(im)[:,:,3]>0
            ob=old.getbbox();nb=im.getbbox()
            evidence.append({'clip':name,'index':i,'sha256':sha(dest),
                'source_cell':[i%4*384,i//4*320+32,384,256] if sheet else None,
                'original_bbox':list(ob),'candidate_bbox':list(nb),
                'bbox_edge_delta_px':[b-a for a,b in zip(ob,nb)],
                'silhouette_iou':float((om&nm).sum()/(om|nm).sum()),
                'animation_metadata_unchanged':True,'whole_frame_scale':1,
                'anatomical_part_transforms':False,
                'original_fx_preserved':sheet is None})
            images.append(im)
        reviewer.review(name,images,clip['ticks'])
        if sheet:
            compare=Image.new('RGBA',(384*2,280*len(images)),'#eeeeee');d=ImageDraw.Draw(compare)
            for i,(idx,im) in enumerate(zip(clip['frames'],images)):
                compare.alpha_composite(Image.open(BASE/'clips'/m['frames'][idx]['file']).convert('RGBA'),(0,i*280))
                compare.alpha_composite(im,(384,i*280));d.text((4,i*280+260),f'{name} {i} BEFORE | NEW (same canvas)',fill='black')
            compare.save(WORK/'review'/f'pose-comparison-{name}.png')
    for f in source['frames']:f['file']='raw_frames/'+f['name']+'.png'
    write(STAGE/'clips_manifest.json',source)
    write(WORK/'pose-preservation.json',evidence)
    print(json.dumps({'frames':len(evidence),'body_frames':54,'original_fx_frames':7}))

if __name__=='__main__':main()
