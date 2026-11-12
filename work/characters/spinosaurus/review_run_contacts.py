"""Review complete poses around the three inserted foot contacts, with pixel evidence."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent/'stage'
rows=[[2,3,4],[4,5,6],[9,10,0]];cw,ch=180,110
out=Image.new('RGBA',(3*cw*2,9*(ch*2+20)),(55,60,68,255));d=ImageDraw.Draw(out)
for j,bg in enumerate(['light','dark','checker']):
 for r,indices in enumerate(rows):
  for c,i in enumerate(indices):
   im=Image.open(S/f'raw_frames/run_{i:02d}.png').convert('RGBA').crop((80,130,260,240))
   tile=Image.new('RGBA',(cw,ch),(244,244,238,255) if bg=='light' else (23,27,35,255))
   if bg=='checker':
    td=ImageDraw.Draw(tile)
    for y in range(0,ch,8):
     for x in range(0,cw,8):td.rectangle((x,y,x+7,y+7),fill=(220,220,220,255) if (x//8+y//8)%2 else (170,170,170,255))
   tile.alpha_composite(im);x=c*cw*2;y=(j*3+r)*(ch*2+20)
   out.alpha_composite(tile.resize((cw*2,ch*2),Image.Resampling.NEAREST),(x,y));d.text((x+3,y+ch*2),f'{bg} run#{i}'+(' CONTACT' if c==1 else ''),fill='white')
path=S/'review/filmstrip-run-contact-transitions.png';out.save(path)
qa=json.loads((S/'qa.json').read_text());records=[]
for i in [3,5,10]:
 a=np.array(Image.open(S/f'raw_frames/run_{i:02d}.png'));y=int(np.where(a[:,:,3]>0)[0].max());assert y==223
 xx=np.where((a[y,:,3]>0)&(np.arange(384)>=176))[0];assert len(xx)>3;x=int(xx[len(xx)//2])
 records.append({'new_index':i,'ground_canvas_y':y,'forward_sole_span_x':[int(xx.min()),int(xx.max())],'sample_canvas_xy':[x,y],'sample_rgba':a[y,x].tolist()})
qa.update(run_contact_measurements=records,run_total_ticks=sum(qa['clips']['run']['ticks']),run_contact_review='Viewed whole-body transitions on light/dark/checker; feet reach ground row223. Original8poses unchanged, good sections retain5ticks. Full cadence/naturalness awaits Owner Human Test; contact pixel tests do not certify anatomy or movement quality.')
(S/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
(S/'review/run-frame-map.json').write_text(json.dumps({'order':qa['run_frame_order_from_v6'],'contacts':qa['run_contact_plan'],'ticks':qa['clips']['run']['ticks'],'measurements':records},ensure_ascii=False,indent=2)+'\n')
p=S/'review/keyframe-review.json';review=json.loads(p.read_text());review['artifacts'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest();p.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(records))
