"""Whole still alpha finishing, uniform size registration and static review boards."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw

W=Path(__file__).resolve().parent;R=W.parents[3]
sys.path.insert(0,str(R/'tools/art'))
from measure_pixel_sharpness import measure

source=Image.open(W/'generated-original.png').convert('RGBA');a=np.array(source)
assert a[0,0,3]<128,'Generated backdrop is not transparent; extract with imagegen before registration.'
a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
whole=Image.fromarray(a);source_box=whole.getbbox();assert source_box
whole=whole.crop(source_box)
assert whole.width<source.width and whole.height<source.height,'Source touches canvas borders'
selected=None
for buffer_width in range(157,162):
    height=round(whole.height*buffer_width/whole.width)
    candidate=whole.resize((buffer_width,height),Image.Resampling.NEAREST)
    b=candidate.getbbox()
    if b and b[2]-b[0]==157:
        selected=candidate.crop(b);break
assert selected is not None,'Cannot register157pxsilhouette with uniformNearest; inspect source.'
canvas=Image.new('RGBA',(384,256));canvas.alpha_composite(selected,(176-selected.width//2,224-selected.height));canvas.save(W/'master.png')
reference=Image.open(R/'assets/sarcosuchus/clips/frames/frame-00.png').convert('RGBA')
ref_box=reference.getbbox();assert ref_box[2]-ref_box[0]==157
for name,color in [('light',(237,236,227)),('dark',(28,31,39)),('checker',(170,170,170))]:
    board=Image.new('RGBA',(768,604),color+(255,));d=ImageDraw.Draw(board)
    if name=='checker':
        for y in range(0,604,16):
            for x in range(0,768,16):
                if (x//16+y//16)%2:d.rectangle((x,y,x+15,y+15),fill=(205,205,205,255))
    ink=(245,245,245) if name=='dark' else (24,24,24)
    d.text((18,12),'Sarcosuchus | 157px | 1x',fill=ink);d.text((402,12),'Chilopoda | 157px | 1x',fill=ink)
    board.alpha_composite(reference,(0,22));board.alpha_composite(canvas,(384,22))
    d.text((18,295),'Sarcosuchus | 2x Nearest',fill=ink);d.text((402,295),'Chilopoda | 2x Nearest',fill=ink)
    for im,x in [(reference,192),(canvas,576)]:
        crop=im.crop(im.getbbox());zoom=crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST);board.alpha_composite(zoom,(x-zoom.width//2,565-zoom.height))
    board.convert('RGB').save(W/f'comparison-{name}.png')
metrics=measure(W/'master.png');metrics.update(art_source='host_image',route='image_gen',source_file='generated-original.png',source_sha256=hashlib.sha256((W/'generated-original.png').read_bytes()).hexdigest(),source_size_px=list(source.size),source_whole_bbox=list(source_box),source_alpha_threshold=128,uniform_registration_buffer_px=[buffer_width,height],reference_character='sarcosuchus',reference_body_bbox=[ref_box[0],ref_box[1],ref_box[2]-ref_box[0],ref_box[3]-ref_box[1]],foot_anchor_px=[176,224],owner_approved=False,technical_checks='static measurements only',motion_quality='not_applicable_static_demo')
(W/'measurements.json').write_text(json.dumps(metrics,indent=2)+'\n')
protected=json.loads((W/'protected-peers.json').read_text());changed=[p for p,h in protected.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];assert not changed,changed
print(json.dumps({'measurements':metrics,'protected_runtime_files_unchanged':len(protected)},indent=2))
