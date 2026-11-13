"""Register complete source poses and independent FX; never deform body parts."""
from pathlib import Path
import json,hashlib,copy,importlib.util
from collections import deque
import numpy as np
from PIL import Image
from scipy import ndimage
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';RAW=S/'raw_frames';RAW.mkdir(parents=True,exist_ok=True)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'plan.json').read_text());master=Image.open(R/plan['master']).convert('RGBA');frames=[];clips={};evidence=[];registered={};source_records={}
def cells(name):
    im=Image.open(W/f'generated/{name}.png').convert('RGBA');a=np.array(im);cols,rows=plan['grids'][name];result=[]
    a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
    labels,n=ndimage.label(a[:,:,3]>0,structure=np.ones((3,3)));areas=np.bincount(labels.ravel());major=[i for i in range(1,n+1) if areas[i]>400]
    expected=plan['body_actions'].get(name,len(plan['ticks'][name]));assert len(major)==expected,(name,'main body count',len(major),expected)
    seed=np.isin(labels,major);nearest=ndimage.distance_transform_edt(~seed,return_distances=False,return_indices=True);owner=labels[tuple(nearest)]
    ordered={}
    for label in major:
        cy,cx=ndimage.center_of_mass(labels==label);index=int(cy//(im.height/rows))*cols+int(cx//(im.width/cols));assert index not in ordered,(name,index);ordered[index]=label
    for i in range(expected):
        x0=round(i%cols*im.width/cols);x1=round((i%cols+1)*im.width/cols);y0=round(i//cols*im.height/rows);y1=round((i//cols+1)*im.height/rows)
        owned=a.copy();owned[(labels==0)|(owner!=ordered[i])]=0;pad=128
        tile=np.array(Image.fromarray(owned).crop((x0-pad,y0-pad,x1+pad,y1+pad)))
        b=Image.fromarray(tile).getbbox();assert b,(name,i,'empty');assert b[0]>0 and b[1]>0 and b[2]<tile.shape[1] and b[3]<tile.shape[0],(name,i,'source clipped',b)
        result.append((tile,list(b),[x0-pad,y0-pad,x1-x0+2*pad,y1-y0+2*pad]))
    return result
idle_cells=cells('idle');b=idle_cells[0][1];base_scale=157/(b[2]-b[0])
def antenna_tips(a):
    mask=a[:,:,3]>0;ys,xs=np.where(mask);xmin,xmax=int(xs.min()),int(xs.max());cut=int(xmin+.90*(xmax-xmin))
    roi=mask.copy();roi[:,:cut]=False;roi=ndimage.binary_closing(roi,structure=np.ones((3,3)))
    labels,n=ndimage.label(roi,structure=np.ones((3,3)));groups=[]
    for label,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        area=int((labels[sl]==label).sum())
        if area>=4:groups.append((area,label))
    groups.sort(reverse=True);assert len(groups)>=2,('antenna components',groups)
    tips=[]
    for _,label in groups[:2]:
        yy,xx=np.where(labels==label);startx=int(xx.min());seeds=[(int(y),startx) for y in yy[xx==startx]];dist={p:0 for p in seeds};queue=deque(seeds)
        while queue:
            y,x=queue.popleft()
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    q=(y+dy,x+dx)
                    if q not in dist and 0<=q[0]<mask.shape[0] and 0<=q[1]<mask.shape[1] and labels[q]==label:
                        dist[q]=dist[(y,x)]+1;queue.append(q)
        end=max(dist,key=dist.get);tips.append([end[1],end[0]])
    return sorted(tips,key=lambda p:p[1])
for name,count in plan['body_actions'].items():
    if name=='turn' and plan['render_contract']['chilopoda'].get('burrow_turn'):
        continue
    cc=cells(name);b0=cc[0][1]
    scale=base_scale if name=='walk' else 157/(b0[2]-b0[0])
    if name=='turn':scale=(registered['walk'][0].getbbox()[2]-registered['walk'][0].getbbox()[0])/(b0[2]-b0[0])
    cols,rows=plan['grids'][name];rootx=(b0[0]+b0[2])/2
    grounds={row:max(box[3] for i,(_,box,_) in enumerate(cc) if i//cols==row) for row in range(rows)}
    ims=[];indices=[];source_records[name]=[]
    for i,(a,box,cell) in enumerate(cc):
        ground=grounds[i//cols]
        if name=='turn':
            # Grounded turn: register nearest bronze leg contact, not antenna bounds.
            rgb=a[:,:,:3].astype(float);legs=(a[:,:,3]>0)&(rgb[:,:,0]>rgb[:,:,1]*1.1)&(rgb[:,:,1]>rgb[:,:,2]*1.35)&(rgb[:,:,1]>35)
            yy,xx=np.where(legs);ground=int(yy.max()+1) if len(yy) else box[3]
        matrix=(1/scale,0,rootx-176/scale,0,1/scale,ground-224/scale)
        out=Image.fromarray(a).transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
        canonical=(name=='idle' and i==0) or (name=='attack_light' and i in [0,15]) or (name=='power_up' and i in [0,11])
        if canonical:out=master.copy()
        if name=='turn' and i==0:out=registered['walk'][0].copy()
        if name=='turn' and i==7:out=registered['walk'][0].transpose(Image.Transpose.FLIP_LEFT_RIGHT).transform((384,256),Image.Transform.AFFINE,(1,0,32,0,1,0),resample=Image.Resampling.NEAREST)
        bb=out.getbbox();assert bb and 0<bb[0]<bb[2]<384 and 0<bb[1]<bb[3]<256,(name,i,bb)
        p=RAW/f'{name}_{i:02d}.png';out.save(p);frames.append({'name':p.stem,'file':'raw_frames/'+p.name});indices.append(len(frames)-1);ims.append(out)
        source_records[name].append({'pixels':a,'scale':scale,'rootx':rootx,'ground':ground,'canonical':canonical})
        labels,n=ndimage.label(a[:,:,3]>0,structure=np.ones((3,3)));evidence.append({'clip':name,'index':i,'source_sheet':f'generated/{name}.png','source_sha256':sha(W/f'generated/{name}.png'),'source_cell':cell,'source_bbox':box,'ownership_components':n,'uniform_action_scale':scale,'source_root_x':rootx,'source_ground_y':ground,'canvas_bbox':list(bb),'canonical_whole_pose':canonical,'body_part_transform':False})
    registered[name]=ims;clips[name]={'frames':indices,'ticks':plan['ticks'][name],'loop_policy':'cycle' if name in ['idle','walk'] else 'oneshot','role':'player'}
    if name=='attack_light':clips[name].update(hitstop_ticks=0,keys={'wind_start':0,'wind_peak':2,'strike':11,'recover':12,'end':15},events=[{'at':6,'name':'custom:burrow_hidden'},{'at':7,'name':'custom:burrow_emerge'},{'at':11,'name':'hit'},{'at':15,'name':'end'}])
    if name=='power_up':clips[name].update(hitstop_ticks=0,keys={'wind_start':0,'wind_peak':3,'strike':4,'recover':8,'end':11},events=[{'at':4,'name':'custom:dual_laser_release'},{'at':11,'name':'end'}])
    if name=='turn':clips[name]['events']=[{'at':0,'name':'in'},{'at':7,'name':'end'}]
# Owner changed turn to burrow/re-emerge; reuse complete own-character poses.
if plan['render_contract']['chilopoda'].get('burrow_turn'):
    poses=[registered['walk'][0]]+[registered['attack_light'][i] for i in [3,4,5,6,7,9,10,11,12]]+[registered['walk'][0]]
    indices=[]
    for i,out in enumerate(poses):
        p=RAW/f'turn_{i:02d}.png';out.save(p);indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name})
    registered['turn']=poses
    clips['turn']={'frames':indices,'ticks':plan['ticks']['turn'],'loop_policy':'oneshot','role':'player','events':[{'at':1,'name':'custom:turn_dive'},{'at':5,'name':'custom:turn_emerge'},{'at':10,'name':'end'}]}
    plan['render_contract']['chilopoda']['burrow_turn']['top_y_by_frame']=[im.getbbox()[1] for im in poses]
    plan['render_contract']['chilopoda']['burrow_turn']['frame_ticks']=plan['ticks']['turn']
tip_evidence=[];tip_anchors=[]
static=np.array(Image.open(W.parent/'demo-v1/generated-original.png').convert('RGBA'));static[:,:,3]=np.where(static[:,:,3]>=128,255,0);static_tips=antenna_tips(static);sb=Image.fromarray(static).getbbox();static_scale=157/(sb[2]-sb[0])
for i,rec in enumerate(source_records['power_up']):
    if rec['canonical']:projected=[[98+(x-sb[0])*static_scale,165+(y-sb[1])*static_scale] for x,y in static_tips]
    else:projected=[[176+(x-rec['rootx'])*rec['scale'],224+(y-rec['ground'])*rec['scale']] for x,y in antenna_tips(rec['pixels'])]
    a=np.array(registered['power_up'][i]);ys,xs=np.where(a[:,:,3]>0);pts=np.stack([xs,ys],axis=1);points=[]
    for point in projected:
        nearest=pts[np.argmin(np.sum((pts-np.array(point))**2,axis=1))];points.append([int(nearest[0]),int(nearest[1])])
    assert points[0]!=points[1],(i,points);tip_anchors.append(points);tip_evidence.append({'frame':i,'projected':projected,'visible_pixel_anchor':points})
plan['render_contract']['chilopoda']['laser']['tip_anchors_by_frame']=tip_anchors
plan['render_contract']['chilopoda']['burrow']['top_y_by_frame']=[im.getbbox()[1] for im in registered['attack_light']]
plan['render_contract']['chilopoda']['burrow']['frame_ticks']=plan['ticks']['attack_light']
write(W/'plan.json',plan)
# Generated FX are registered as complete effects, independently from body.
for name in plan['render_contract']['effect_clips']:
    src=Image.open(W/f'generated/{name}.png').convert('RGBA');cols,rows=plan['grids'][name];tiles=[];bounds=[]
    for i in range(len(plan['ticks'][name])):
        x0=round(i%cols*src.width/cols);x1=round((i%cols+1)*src.width/cols);y0=round(i//cols*src.height/rows);y1=round((i//cols+1)*src.height/rows)
        tile=src.crop((x0,y0,x1,y1));a=np.array(tile);a[a[:,:,3]<8]=0;tile=Image.fromarray(a);b=tile.getbbox();assert b,(name,i);tiles.append(tile);bounds.append(b)
    indices=[];ims=[]
    if name=='burrow_dust_fx':
        maxw=max(b[2]-b[0] for b in bounds);maxh=max(b[3]-b[1] for b in bounds);scale=min(64/maxw,32/maxh)
    elif name=='red_laser_fx':scale=20/max(b[2]-b[0] for b in bounds)
    for i,tile in enumerate(tiles):
        out=Image.new('RGBA',(384,256));b=bounds[i]
        if name=='antenna_glow_fx':
            small=tile.resize((13,13),Image.Resampling.NEAREST);out.alpha_composite(small,(170,122))
        else:
            # Shared scale, source cell center and source ground/center for all phases.
            if name=='burrow_dust_fx':
                source_ground=max(bounds[j][3] for j in range(i//cols*cols,min((i//cols+1)*cols,len(bounds))))
                matrix=(1/scale,0,tile.width/2-176/scale,0,1/scale,source_ground-128/scale)
            else:matrix=(1/scale,0,tile.width/2-176/scale,0,1/scale,tile.height/2-128/scale)
            out=tile.transform((384,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST)
        assert out.getbbox(),(name,i,'FX vanished')
        p=RAW/f'{name}_{i:02d}.png';out.save(p);indices.append(len(frames));frames.append({'name':p.stem,'file':'raw_frames/'+p.name});ims.append(out)
    registered[name]=ims;clips[name]={'frames':indices,'ticks':plan['ticks'][name],'loop_policy':'oneshot','role':'fx'}
manifest={'schema':'generate2dsprite.animation_clips.v2','art_source':'host_image','pixel_art':True,'sampling':'nearest','body_height_px':59,'anchor_px':[176,224],'shadow':{'rx':38,'ry':4,'opacity':.3},'frames':frames,'clips':clips,'states':{'idle':'idle','moving':'walk','turn':'turn','attack':'attack_light','power':'power_up','hurt':'hit','dead':'ko'}}
write(S/'clips_manifest.json',manifest);write(W/'registration.json',evidence);write(W/'antenna-anchor-proof.json',tip_evidence)
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
for name,ims in registered.items():rv.review(name,ims,plan['ticks'][name])
if not plan['render_contract']['chilopoda'].get('burrow_turn'):
    reverse=[im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transform((384,256),Image.Transform.AFFINE,(1,0,32,0,1,0),resample=Image.Resampling.NEAREST) for im in registered['turn']];rv.review('turn-left-to-right',reverse,plan['ticks']['turn'])
print(json.dumps({'frames':len(frames),'clips':len(clips),'base_scale':base_scale,'tip_anchors':tip_anchors}))
