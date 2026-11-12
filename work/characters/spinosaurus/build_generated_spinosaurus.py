#!/usr/bin/env python3
"""Repack the Owner-approved whole frames. Run is deliberately excluded."""
import json,hashlib,shutil,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
WORK=Path(__file__).resolve().parent
STAGE=WORK/'stage'
SOURCE=WORK/'approved-final-frames'
SIZE=(384,256);ANCHOR=(176,224)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def bbox(a):
 y,x=np.where(a[:,:,3]>0)
 return {'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
MANIFEST=json.loads((SOURCE/'manifest.json').read_text())
TICKS={n:c['ticks'] for n,c in MANIFEST['clips'].items()}
def reviews(rendered):
 out=STAGE/'review';out.mkdir(exist_ok=True)
 for name,frames in rendered.items():
  boxes=[bbox(a) for a in frames];x0=min(b['x'] for b in boxes)-6;y0=min(b['y'] for b in boxes)-6
  x1=max(b['x']+b['w'] for b in boxes)+6;y1=max(b['y']+b['h'] for b in boxes)+6
  cw,ch=x1-x0,y1-y0;cols=min(6,len(frames));rows=math.ceil(len(frames)/cols)
  sheet=Image.new('RGBA',(cols*(cw*2+4),3*(rows*(ch*2+18)+22)),(55,60,68,255));d=ImageDraw.Draw(sheet)
  for k,bg in enumerate(['light','dark','checker']):
   top=k*(rows*(ch*2+18)+22);d.text((3,top+3),name+' / '+bg+' / 60Hz',fill='white')
   for i,a in enumerate(frames):
    tile=Image.new('RGBA',(cw,ch),(244,244,238,255) if bg=='light' else (23,27,35,255))
    if bg=='checker':
     td=ImageDraw.Draw(tile)
     for y in range(0,ch,8):
      for x in range(0,cw,8):td.rectangle((x,y,x+7,y+7),fill=(220,220,220,255) if (x//8+y//8)%2 else (170,170,170,255))
    tile.alpha_composite(Image.fromarray(a).crop((x0,y0,x1,y1)))
    x=i%cols*(cw*2+4);y=top+22+i//cols*(ch*2+18)
    sheet.alpha_composite(tile.resize((cw*2,ch*2),Image.Resampling.NEAREST),(x,y));d.text((x,y+ch*2),f'#{i} {TICKS[name][i]:g} ticks',fill='white')
  sheet.save(out/f'filmstrip-{name}.png')
  pics=[]
  for a in frames:
   tile=Image.new('RGBA',SIZE,(238,238,230,255));tile.alpha_composite(Image.fromarray(a));pics.append(tile.resize((768,512),Image.Resampling.NEAREST))
  pics[0].save(out/f'playback-{name}.webp',save_all=True,append_images=pics[1:],duration=[round(t*1000/60) for t in TICKS[name]],loop=0,lossless=True)

def main():
 if STAGE.exists():shutil.rmtree(STAGE)
 (STAGE/'raw_frames').mkdir(parents=True)
 for f in MANIFEST['frames']:shutil.copyfile(SOURCE/(f['name']+'.png'),STAGE/f['file'])
 write(STAGE/'clips_manifest.json',MANIFEST)
 qa=json.loads((SOURCE/'qa-source.json').read_text());write(STAGE/'qa.json',qa)
 rendered={n:[np.array(Image.open(STAGE/'raw_frames'/(f+'.png'))) for f in c['frames']] for n,c in MANIFEST['clips'].items()}
 reviews(rendered)
 print(json.dumps({'frames':len(MANIFEST['frames']),'clips':len(TICKS),'removed':'run','source':'Owner approved unchanged whole frames'}))
if __name__=='__main__':main()
