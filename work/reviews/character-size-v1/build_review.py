"""Whole-frame size/alpha normalization for Owner review; no atlas/animation edits."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/art'))
from measure_pixel_sharpness import measure
sources={'spinosaurus':R/'assets/spinosaurus/clips/frames/frame-00.png','pteranodon':R/'assets/pteranodon/clips/frames/frame-00.png','tasmanian_king_crab':R/'work/characters/tasmanian_king_crab/master-review/concept-v2.png'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={};images={}
for cid,p in sources.items():
 im=Image.open(p).convert('RGBA');source_bbox=im.getchannel('A').getbbox();threshold=None
 if cid=='spinosaurus':
  result=im;scale=1;anchor=[176,224]
 else:
  # Source transparency only; no chroma mask, limb cuts, RGB change, palette, blur or sharpening.
  if cid=='tasmanian_king_crab':
   threshold=128;a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=threshold,255,0);a[a[:,:,3]==0,:3]=0;im=Image.fromarray(a)
  bbox=im.getchannel('A').getbbox();crop=im.crop(bbox);target_w=157 if cid=='pteranodon' else round(157*.85);scale=target_w/crop.width
  # A one-pixel extremity can disappear under nearest sampling. Find the closest
  # uniform whole-image size whose measured silhouette has the requested width.
  nominal_scale=scale
  for sampled_w in [target_w,target_w+1,target_w-1,target_w+2]:
   scale=sampled_w/crop.width;target_h=round(crop.height*scale)
   body=crop.resize((sampled_w,target_h),Image.Resampling.NEAREST)
   sampled_bbox=body.getchannel('A').getbbox()
   if sampled_bbox[2]-sampled_bbox[0]==target_w:break
  else:raise ValueError('Cannot achieve requested silhouette width with uniform nearest sampling')
  anchor=[176,200] if cid=='pteranodon' else [176,224]
  if cid=='pteranodon':left=round(anchor[0]-(176-bbox[0])*scale);top=round(anchor[1]-(200-bbox[1])*scale)
  else:left=round(anchor[0]-target_w/2);top=anchor[1]-target_h
  result=Image.new('RGBA',(384,256));result.paste(body,(left,top))
  assert result.getchannel('A').getbbox() is not None
 dest=OUT/f'{cid}-sample.png';result.save(dest);m=measure(dest)
 assert m['visible_alpha_hardness_pct']==100
 assert m['canvas_size_px']==[384,256]
 assert m['body_bbox_px'][2]=={'spinosaurus':157,'pteranodon':157,'tasmanian_king_crab':133}[cid]
 images[cid]=result
 records[cid]={'source':str(p.relative_to(R)),'source_sha256':sha(p),'source_alpha_nonzero_bbox_xyxy':source_bbox,'alpha_threshold':threshold,'scale':scale,'sampling':'Nearest','anchor_px':anchor,'sample':str(dest.relative_to(R)),'metrics':m}
# Review boards are visual evidence only, not engine textures.
for bg in ['light','dark','checker']:
 board=Image.new('RGB',(1152,304),'#eee8dc' if bg=='light' else '#171a20');draw=ImageDraw.Draw(board)
 if bg=='checker':
  for y in range(0,304,16):
   for x in range(0,1152,16):draw.rectangle((x,y,x+15,y+15),fill='#b9b9b9' if (x//16+y//16)%2 else '#dddddd')
 for n,(cid,im) in enumerate(images.items()):
  x=n*384;board.paste(im,(x,24),im);d=ImageDraw.Draw(board);col='#161616' if bg!='dark' else '#eeeeee';bbox=records[cid]['metrics']['body_bbox_px'];d.text((x+12,8),f'{cid}  {bbox[2]} x {bbox[3]} px',fill=col);d.line((x+4,248,x+379,248),fill='#828282');d.text((x+12,282),'1x / nearest; common canvas 384x256',fill=col)
 board.save(OUT/f'comparison-{bg}.png')
(OUT/'measurements.json').write_text(json.dumps({'status':'ready_for_owner_size_review','size_axis':'idle0 full-body width; include wings/legs/claws, exclude FX','reference_width_px':157,'tasmanian_ideal_width_px':133.45,'tasmanian_actual_width_px':133,'tasmanian_actual_reduction_pct':100*(1-133/157),'rounding':'nearest whole pixel; preserve source aspect with <=0.5px height rounding','characters':records,'processing':'Whole-frame crop/resample/placement and source-alpha binarization only. No body part manipulation or AI redraw. Original files unchanged.','limits':['Size and hard alpha measured; perceived pixel-art finish and anatomy require Owner review.','Static size review only; no atlas or animation generated/modified.','Sobel values are measured evidence, not a target or automatic acceptance.']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({cid:r['metrics'] for cid,r in records.items()},ensure_ascii=False,indent=2))
