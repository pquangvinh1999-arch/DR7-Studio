"""Normalize the complete edited pose at the existing master's fixed scale/root."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw
import numpy as np
W=Path(__file__).resolve().parent;R=W.parents[4];v1=json.load(open(W.parent/'master-review.json'));scale=v1['body_scale'];root=v1['source_root_x'];ground=v1['source_subject_bbox_xyxy'][3]
a=np.array(Image.open(W/'concept-v2.png').convert('RGBA'));mask=a[:,:,3]>=128;a[:,:,3]=mask*255;a[~mask]=0
out=Image.fromarray(a).transform((384,256),Image.Transform.AFFINE,(1/scale,0,root-176/scale,0,1/scale,ground-224/scale),resample=Image.Resampling.NEAREST);out.save(W/'master-gameplay-v2.png');sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=measure(W/'master-gameplay-v2.png');assert metrics['visible_alpha_hardness_pct']==100;b=out.getbbox();assert b[0]>0 and b[1]>0 and b[2]<384 and b[3]<256
old=Image.open(W.parent/'master-gameplay-v1.png').convert('RGBA')
for bg in ['light','dark','checker']:
 board=Image.new('RGB',(768,584),'#eee8dc' if bg=='light' else '#171b23');d=ImageDraw.Draw(board);fg='#eee' if bg=='dark' else '#191919'
 if bg=='checker':
  for y in range(0,584,12):
   for x in range(0,768,12):d.rectangle((x,y,x+11,y+11),fill='#bbb' if (x//12+y//12)%2 else '#ddd')
 for n,(name,im) in enumerate([('Original master',old),('Two neck frills',out)]):
  x=n*384;bb=im.getbbox();board.paste(im,(x,20),im);d.text((x+8,6),f'{name}: {bb[2]-bb[0]} x {bb[3]-bb[1]} px / 1x',fill=fg);d.line((x+4,244,x+379,244),fill='#999');detail=im.crop((bb[0]-3,bb[1]-3,bb[2]+3,bb[3]+3));detail=detail.resize((detail.width*2,detail.height*2),Image.Resampling.NEAREST);board.paste(detail,(x+22,320),detail);d.text((x+8,294),'2x nearest detail (review only)',fill=fg)
 board.save(W/f'comparison-{bg}.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof={'status':'frill_revision_pending_owner','art_source':'built-in imagegen edit','edit_target':'work/characters/dilophosaurus/master-review/concept-v1.png','frill_reference':'work/characters/dilophosaurus/master-review/image.png','reference_sha256':sha(W.parent/'image.png'),'source_sha256':sha(W/'concept-v2.png'),'source_size_px':[a.shape[1],a.shape[0]],'source_alpha_threshold':128,'fixed_scale_from_v1':scale,'source_root_x':root,'source_ground_y':ground,'canvas_size_px':[384,256],'foot_anchor_px':[176,224],'metrics':metrics,'limits':'Generated edit preserves visual identity and pose by reference; does not claim original body pixels remained byte-identical. No body-part cut/warp. Paired frill design is explicitly requested game styling. Master only; no animation/roster admission.'};(W/'master-review.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(proof,ensure_ascii=False))
