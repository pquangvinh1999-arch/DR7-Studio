"""Register complete generated Bat poses; preserve source sonic geometry with a purple palette."""
from pathlib import Path
import json,hashlib,copy,importlib.util,sys,colorsys
import numpy as np
from PIL import Image
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';RAW=S/'raw_frames';RAW.mkdir(parents=True,exist_ok=True)
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'plan.json').read_text());source=json.loads((W/'source/pteranodon-source-manifest.json').read_text());ref=json.loads((W/'source/pteranodon-animation-clips.json').read_text())
idle=np.array(Image.open(W/'generated/idle.png').convert('RGBA'));assert idle.shape==(1024,1536,4)
mask=idle[:512,:384,3]>=128;ys,xs=np.where(mask);source0=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
scale=126/(source0[2]-source0[0]);rootx=(source0[0]+source0[2])/2;rooty=source0[3]
evidence=[];frames=[]
for name,count in plan['body_actions'].items():
    a=np.array(Image.open(W/f'generated/{name}.png').convert('RGBA'));assert a.shape==(1024,1536,4),(name,a.shape)
    a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
    for i in range(count):
        x0=i%4*384;y0=i//4*512;tile=a[y0:y0+512,x0:x0+384].copy();m=tile[:,:,3]>0;ys,xs=np.where(m)
        assert len(xs),(name,i,'empty');b=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        assert b[0]>2 and b[1]>2 and b[2]<382 and b[3]<510,(name,i,'clipped',b)
        # Retain every owned source component; never cut apart body parts or mask
        # with a different character. Grid gutters are verified empty above.
        labels,n=ndimage.label(m);areas=np.bincount(labels.ravel())[1:]
        complete=Image.fromarray(tile)
        matrix=(1/scale,0,rootx-176/scale,0,1/scale,rooty-200/scale)
        out=complete.transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
        canonical=name=='idle' and i==0
        if canonical:out=Image.open(R/plan['master']).convert('RGBA')
        bb=out.getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<384 and bb[3]<256,(name,i,bb)
        file=f'{name}_{i:02d}.png';out.save(RAW/file);frames.append({'name':file[:-4],'file':'raw_frames/'+file})
        evidence.append({'clip':name,'index':i,'source_sheet':f'generated/{name}.png','source_sha256':sha(W/f'generated/{name}.png'),'source_cell':[x0,y0,384,512],'source_bbox':b,'components':len(areas),'largest_component_px':int(areas.max()),'global_scale':scale,'source_registration_root':[rootx,rooty],'canvas_bbox':list(bb),'whole_master_reuse':canonical,'body_part_transform':False})
# Take hue from imagegen's requested purple recolor. Keep original seven phase
# geometries and alpha exactly; palette projection avoids generative geometry drift.
purple=np.array(Image.open(W/'generated/sonic_screech_fx.png').convert('RGBA'));rgb=purple[:,:,:3].astype(float)/255;valid=(purple[:,:,3]>128)&(rgb.max(2)-rgb.min(2)>.25)
hues=np.array([colorsys.rgb_to_hsv(*p)[0] for p in rgb[valid]])
purple_hue=float(np.median(hues[(hues>.65)&(hues<.9)]));assert .65<purple_hue<.9,purple_hue
fxproof=[]
for i,idx in enumerate(ref['clips']['sonic_screech_fx']['frames']):
    src=R/'assets/pteranodon/clips'/ref['frames'][idx]['file'];im=Image.open(src).convert('RGBA');arr=np.array(im);color=arr[:,:,:3].copy()
    # Color substitution only on existing FX; preserve luminance hierarchy,
    # saturation, every original silhouette, alpha value and phase registration.
    for c in np.unique(color[arr[:,:,3]>0],axis=0):
        h,s,v=colorsys.rgb_to_hsv(*(c/255));new=np.rint(np.array(colorsys.hsv_to_rgb(purple_hue,s,v))*255).astype('uint8');sel=np.all(color==c,axis=2)&(arr[:,:,3]>0);arr[:,:,:3][sel]=new
    recolor=Image.fromarray(arr)
    # Same whole-FX80% size map about its source pivot; no body or limb editing.
    pivot=(176,141);recolor=recolor.transform((384,256),Image.Transform.AFFINE,(1/.8,0,pivot[0]-pivot[0]/.8,0,1/.8,pivot[1]-pivot[1]/.8),resample=Image.Resampling.NEAREST)
    file=f'sonic_screech_fx_{i:02d}.png';recolor.save(RAW/file);frames.append({'name':file[:-4],'file':'raw_frames/'+file})
    fxproof.append({'phase':i,'source':str(src.relative_to(R)),'source_sha256':sha(src),'palette_only_before_scale':True,'source_alpha_preserved_before_scale':bool(np.array_equal(arr[:,:,3],np.array(im)[:,:,3])),'hue_from_imagegen':purple_hue,'uniform_fx_scale':.8})
manifest=copy.deepcopy(source);manifest.update(body_height_px=81,anchor_px=[176,200],shadow={'rx':22,'ry':5,'opacity':.3},frames=frames)
write(S/'clips_manifest.json',manifest);write(W/'registration.json',evidence);write(W/'fx-source-evidence.json',{'palette_source':'generated/sonic_screech_fx.png','palette_source_sha256':sha(W/'generated/sonic_screech_fx.png'),'purple_hue':purple_hue,'phases':fxproof})
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for n,c in manifest['clips'].items():
    ims=[Image.open(RAW/(name+'.png')).convert('RGBA') for name in c['frames']];rv.review(n,ims,c['ticks'])
write(W/'registration-summary.json',{'scale':scale,'source0bbox':source0,'shared_root':[rootx,rooty],'frame_count':len(frames),'clip_count':len(manifest['clips'])})
print(json.dumps({'frames':len(frames),'clips':len(manifest['clips']),'scale':scale,'source0':source0,'purple_hue':purple_hue}))
