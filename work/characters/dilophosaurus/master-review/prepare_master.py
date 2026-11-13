"""Static master preparation: source alpha, one whole-pose scale and registration."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3]
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
p=W/'concept-v1.png';a=np.array(Image.open(p).convert('RGBA'));raw_alpha=[int(a[:,:,3].min()),int(a[:,:,3].max())];mask=a[:,:,3]>=128;a[:,:,3]=mask*255;a[~mask,:3]=0;im=Image.fromarray(a);bbox=im.getchannel('A').getbbox();crop=im.crop(bbox)
# Register to the dark body mass in the dense torso columns, excluding thin tail.
cols=mask.sum(axis=0);cut=float(.6*np.percentile(cols[cols>0],95));dense=cols>=cut;lab,_=ndimage.label(dense);sizes=np.bincount(lab);sizes[0]=0;dense=lab==np.argmax(sizes);torso=mask&dense[None,:]&(a[:,:,:3].max(axis=2)<80);root_x=float(np.median(np.where(torso)[1]))
for width in [157,158,159,156,160,161,162]:
 scale=width/crop.width;body=crop.resize((width,round(crop.height*scale)),Image.Resampling.NEAREST);b=body.getchannel('A').getbbox()
 if b[2]-b[0]==157:break
else:raise ValueError('Could not preserve full-body silhouette width157 after raster sampling')
left=round(176-(root_x-bbox[0])*scale);top=224-b[3]
out=Image.new('RGBA',(384,256));out.paste(body,(left,top));out.save(W/'master-gameplay-v1.png');metrics=measure(W/'master-gameplay-v1.png')
assert metrics['body_bbox_px'][2]==157;assert metrics['visible_alpha_hardness_pct']==100;assert metrics['canvas_size_px']==[384,256]
spino=Image.open(R/'assets/spinosaurus/clips/frames/frame-00.png').convert('RGBA')
for bg in ['light','dark','checker']:
 board=Image.new('RGB',(768,584),'#eee8dc' if bg=='light' else '#171b23');d=ImageDraw.Draw(board);fg='#191919' if bg!='dark' else '#eeeeee'
 if bg=='checker':
  for y in range(0,584,12):
   for x in range(0,768,12):d.rectangle((x,y,x+11,y+11),fill='#bbbbbb' if (x//12+y//12)%2 else '#dddddd')
 for n,(name,pic) in enumerate([('Spinosaurus',spino),('Dilophosaurus',out)]):
  x=n*384;b=pic.getbbox();board.paste(pic,(x,20),pic);d.text((x+8,6),f'{name} {b[2]-b[0]} x {b[3]-b[1]} px / 1x',fill=fg);d.line((x+4,244,x+379,244),fill='#999999')
  # 2x crop view, no artwork modification; sizes are explicitly labelled.
  close=pic.crop((b[0]-3,b[1]-3,b[2]+3,b[3]+3));close=close.resize((close.width*2,close.height*2),Image.Resampling.NEAREST);board.paste(close,(x+22,320),close);d.text((x+8,294),'2x nearest detail (review only)',fill=fg)
 board.save(W/f'comparison-{bg}.png')
proof={'status':'master_pending_owner','art_source':'built-in imagegen','source':str(p.relative_to(R)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_canvas_size_px':[a.shape[1],a.shape[0]],'source_alpha_range':raw_alpha,'source_alpha_binarization_threshold':128,'source_subject_bbox_xyxy':list(bbox),'source_root_x':root_x,'root_detector':'Median darkRGBmax<80 in largest dense-body column interval; density threshold0.6*95thpercentile column occupancy. Used only for whole-pose registration, not to repaint art.','body_scale':scale,'sampled_buffer_size_px':list(body.size),'source_aspect_preserved':'Whole-pose uniform scale, outputheight rounded to a whole pixel; silhouettewidth measured afterNearest. No per-axis stretch or limb/part editing.','canvas_size_px':[384,256],'foot_anchor_px':[176,224],'metrics':metrics,'size_rule':'Proposed review width157px against Spinosaurus; preserve Dilophosaurus natural aspect. Owner has not approved size.','limits':['Static master only; no animation/atlas/roster admission.','Sobel measured but not forced to match a scalar; perceivedfinish/anatomy pendingOwner.','Game palette is an artistic choice, not a claim of palaeocolour.']}
(W/'master-review.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(proof,ensure_ascii=False,indent=2))
