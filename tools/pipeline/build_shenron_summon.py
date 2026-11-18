#!/usr/bin/env python3
"""Extract Owner source items, preserving interiors; no AI redraw or limb rigging."""
from pathlib import Path
import hashlib,json,random,shutil
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/rituals/shenron_summon'
WORK=ROOT/'docs/contracts/shenron_summon'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def extract(rgb,component):
    owned=ndimage.binary_fill_holes(component)
    # Component ownership excludes neighbouring poses; extend only its antialiased rim.
    support=ndimage.binary_dilation(owned,iterations=2)&(rgb.min(axis=2)<254)
    inner=ndimage.binary_erosion(owned,iterations=2)
    inner_idx=ndimage.distance_transform_edt(~inner,return_distances=False,return_indices=True)
    outside=~ndimage.binary_dilation(owned,iterations=3)
    bg_idx=ndimage.distance_transform_edt(~outside,return_distances=False,return_indices=True)
    fg=rgb[tuple(inner_idx)].astype(float)
    bg=rgb[tuple(bg_idx)].astype(float)
    c=rgb.astype(float);v=bg-fg
    alpha=np.clip(np.sum((bg-c)*v,axis=2)/np.maximum(1,np.sum(v*v,axis=2)),0,1)
    rgba=np.zeros((*rgb.shape[:2],4),np.uint8)
    rgba[owned,:3]=rgb[owned];rgba[owned,3]=255
    ring=support&~ndimage.binary_erosion(owned)
    valid=ring&(alpha>0.02)
    rgba[valid,:3]=np.clip((c[valid]-bg[valid]*(1-alpha[valid,None]))/alpha[valid,None],0,255).round().astype('uint8')
    rgba[valid,3]=(alpha[valid]*255).round().astype('uint8')
    yy,xx=np.where(rgba[:,:,3]>0)
    box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
    return Image.fromarray(rgba).crop(box),box,owned

def build():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'items').mkdir(exist_ok=True)
    (OUT/'source').mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    src1=ROOT/'image copy.png' if (ROOT/'image copy.png').is_file() else OUT/'source'/'owner-1.png'
    src2=ROOT/'image copy 2.png' if (ROOT/'image copy 2.png').is_file() else OUT/'source'/'owner-2.png'
    sources=[src1,src2]
    for i,p in enumerate(sources):
        dst=OUT/'source'/f'owner-{i+1}.png'
        if p.resolve()!=dst.resolve():shutil.copy2(p,dst)
    sources=[OUT/'source'/'owner-1.png',OUT/'source'/'owner-2.png']
    rgb=np.array(Image.open(sources[0]).convert('RGB'));v=rgb.astype(int)
    seed=(v.max(2)-v.min(2)>20)|(v.max(2)<100)
    labels,_=ndimage.label(seed);records={};images={}
    for label,size in enumerate(np.bincount(labels.ravel())):
        if label==0 or size<500:continue
        component=labels==label;yy,xx=np.where(component)
        roi=v[yy.min():yy.max()+1,xx.min():xx.max()+1]
        stars=(roi[:,:,0]>90)&(roi[:,:,0]<210)&(roi[:,:,1]<80)&(roi[:,:,0]-roi[:,:,1]>55)
        sl,_=ndimage.label(stars);areas=[int(n) for n in np.bincount(sl.ravel())[1:] if n>150]
        number=len(areas);assert number in range(1,8) and number not in records
        # Work in a small ownership crop, leaving the source's other balls entirely untouched.
        x0=max(0,int(xx.min())-4);y0=max(0,int(yy.min())-4);x1=min(rgb.shape[1],int(xx.max())+5);y1=min(rgb.shape[0],int(yy.max())+5)
        im,box,owned=extract(rgb[y0:y1,x0:x1],component[y0:y1,x0:x1]);box=[box[0]+x0,box[1]+y0,box[2]+x0,box[3]+y0]
        key=f'ball_{number}';images[key]=im
        path=OUT/'items'/f'dragon-ball-{number:02d}.png';im.save(path)
        records[key]={'star_count':number,'star_component_areas':areas,'source_box_xyxy':box,'source_center_px':[(box[0]+box[2])/2,(box[1]+box[3])/2],'file':str(path.relative_to(ROOT)),'sha256':digest(path)}
    assert set(records)=={f'ball_{i}' for i in range(1,8)}
    rgb2=np.array(Image.open(sources[1]).convert('RGB'));v=rgb2.astype(int);seed=(v.max(2)-v.min(2)>20)|(v.max(2)<100)
    labels,_=ndimage.label(seed);sizes=np.bincount(labels.ravel());sizes[0]=0
    im,box,owned=extract(rgb2,labels==int(sizes.argmax()))
    # One premultiplied area reduction to native gameplay texels; hard item alpha.
    native_source=im.copy();target=(144,round(im.height*144/im.width))
    a=np.array(im,dtype=np.float32)/255.;alpha=a[:,:,3]
    reduced_alpha=np.array(Image.fromarray(alpha,mode='F').resize(target,Image.Resampling.BOX))
    out=np.zeros((target[1],target[0],4),dtype=np.uint8);solid=reduced_alpha>=0.5
    for channel in range(3):
        premul=np.array(Image.fromarray(a[:,:,channel]*alpha,mode='F').resize(target,Image.Resampling.BOX))
        out[:,:,channel]=np.where(solid,np.clip(premul/np.maximum(reduced_alpha,1e-8)*255,0,255).round(),0).astype('uint8')
    out[:,:,3]=solid.astype('uint8')*255
    im=Image.fromarray(out);images['ground']=im
    im.save(OUT/'ground-cluster.png');records['ground']={'source_box_xyxy':box,'file':str((OUT/'ground-cluster.png').relative_to(ROOT)),'sha256':digest(OUT/'ground-cluster.png'),'source_size_px':list(native_source.size),'native_pixel_size_px':list(im.size),'finish':'single premultiplied BOX area reduction; alpha>=0.5 hard; native1px; Nearest; no redraw, sharpening, dithering or forced palette'}
    # Independent VFX from the actual cluster silhouette; original item art is unchanged.
    h=round(256*im.height/im.width);mask=im.getchannel('A').resize((256,h),Image.Resampling.LANCZOS)
    glow_mask=Image.new('L',(320,h+64),0);glow_mask.paste(mask,(32,32));glow_mask=glow_mask.filter(ImageFilter.GaussianBlur(11))
    glow=Image.new('RGBA',glow_mask.size,(255,220,112,0));glow.putalpha(glow_mask);images['glow']=glow;glow.save(OUT/'glow.png')
    core=Image.new('RGBA',glow.size,(255,255,235,0));core.putalpha(glow_mask);images['core']=core;core.save(OUT/'core.png')
    # One shared page; native source crop pixels are copied exactly into every region.
    atlas=Image.new('RGBA',(2048,2048),(0,0,0,0));regions={};x=y=2;rowh=0
    for key in [*(f'ball_{i}' for i in range(1,8)),'ground','glow','core']:
        image=images[key]
        if x+image.width+2>2048:x=2;y+=rowh+4;rowh=0
        assert y+image.height+2<=2048
        atlas.paste(image,(x,y));regions[key]=[x,y,image.width,image.height]
        x+=image.width+4;rowh=max(rowh,image.height)
    atlas.save(OUT/'atlas.png')
    all_boxes=[records[f'ball_{i}']['source_box_xyxy'] for i in range(1,8)]
    layout_center=[(min(b[0] for b in all_boxes)+max(b[2] for b in all_boxes))/2,(min(b[1] for b in all_boxes)+max(b[3] for b in all_boxes))/2]
    layout_scale=64/330
    items=[]
    for i in range(1,8):
        key=f'ball_{i}';r=records[key];cx,cy=r['source_center_px'];items.append({'number':i,'region':regions[key],'file':r['file'],'source_box_xyxy':r['source_box_xyxy'],'formation_offset_px':[(cx-layout_center[0])*layout_scale,(cy-layout_center[1])*layout_scale]})
    mask_ranks=list(range(96*68));random.Random(17013).shuffle(mask_ranks)
    mask_values=[int(rank*256/len(mask_ranks)) for rank in mask_ranks]
    mask_img=Image.new('RGBA',(96,68));mask_img.putdata([(v,v,v,255) for v in mask_values])
    mask_path=OUT/'dissolve-threshold.png';mask_img.save(mask_path)
    reveal={'method':'pixel_dissolve','mask':str(mask_path.relative_to(ROOT)),'mask_sha256':digest(mask_path),'mask_size_px':[96,68],'cell_size_canvas_px':4,'threshold_levels':256,'edge_width':0.07,'edge_color_rgb':[255,236,156]}
    config={'schema':'dr7.shenron_summon.v5','tick_hz':60,'atlas':'assets/rituals/shenron_summon/atlas.png','atlas_sha256':digest(OUT/'atlas.png'),'items':items,'regions':regions,'sampling':'nearest','source_images':[{'file':str(p.relative_to(ROOT)),'sha256':digest(p),'size':list(Image.open(p).size)} for p in sources],
      'timeline':{'launch_stride_ticks':18,'flight_ticks':54,'last_arrival_tick':162,'gather_hold_ticks':48,'vanish_start_tick':210,'flash_start_ticks':[228,246],'flash_rise_ticks':2,'flash_hold_ticks':4,'flash_fall_ticks':4,'ground_start_tick':246,'ground_fade_ticks':2,'dragon_start_tick':246,'dragon_reveal_curve':'ease_out_quad','ready_tick':258,'glow_period_ticks':48},
      'dismiss_timeline':{'flash_start_ticks':[0,18],'flash_rise_ticks':2,'flash_hold_ticks':4,'flash_fall_ticks':4,'vanish_tick':20,'end_tick':28},
      'wishes':[
        {'id':'heal_full','label':'1. Hồi đầy Sinh Lực & Ki','notice':'Shenron đã nhận điều ước: Hồi đầy Sinh Lực & Ki!'},
        {'id':'max_power','label':'2. Bộc phát Sức Mạnh Cực Đại','notice':'Shenron đã nhận điều ước: Bộc phát Sức Mạnh Cực Đại!'},
        {'id':'wealth_gems','label':'3. Ban thưởng Ngọc Rồng & Vàng','notice':'Shenron đã nhận điều ước: Ban thưởng Ngọc Rồng & Vàng!'},
      ],
      'layout':{'map_center_px':[960,540],'ground_y':840,'ball_display_width_px':64,'formation_reference_scale':layout_scale,'flight_arc_height_px':150,'ground_display_width_px':144,'dragon_scale':2.76,'dragon_reference_bottom_canvas_y':228,'dragon_gap_px':0,'dragon_reveal_rise_px':48,'aura_width_px':420,'aura_height_px':540},
      'behavior':{'trigger':'button_only','freeze_caster_during_sequence':True,'persist_until_dismissed':True,'block_retrigger_while_active':True,'requires_seven_balls_in_gameplay':True,'test_mode_bypass_ball_requirement':True,'auto_dismiss_after_wish':True,'dragon_character_id':'shenron','dragon_clip':'idle','body_bundle':'assets/shenron/godot_bundle/engine-export.json'},
      'qa':{'art_source':'existing_owner_images','method':'2D component ownership; enclosed highlight preservation; white/gray1px edge unmixing','source1_items_detected':7,'star_counts':[r['star_count'] for k,r in sorted(records.items()) if k.startswith('ball_')],'ground_orientation':'source orientation preserved; no AI redraw or geometric repair','glow_source':'derived alpha silhouette only; independent VFX','revision':'v5-dismiss-flash-wish','status':'owner_approved'},
      'reveal':reveal}
    (OUT/'sequence.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    (WORK/'evidence/extraction.json').write_text(json.dumps({'sources':config['source_images'],'items':records,'layout_center_source_px':layout_center,'regions':regions},ensure_ascii=False,indent=2)+'\n')
    review=Image.new('RGB',(800,720),(28,32,42));draw=ImageDraw.Draw(review)
    for i in range(1,8):
        thumb=images[f'ball_{i}'].copy();thumb.thumbnail((125,125),Image.Resampling.NEAREST);xx=20+((i-1)%4)*190;yy=25+((i-1)//4)*180;review.paste(thumb,(xx,yy),thumb);draw.text((xx,yy+130),f'{i} stars',fill='white')
    cluster=images['ground'].copy();cluster.thumbnail((300,300),Image.Resampling.NEAREST);review.paste(cluster,(250,390),cluster);review.save(WORK/'evidence/extraction-review.png')
    print(json.dumps({'atlas':str(OUT/'atlas.png'),'item_count':7,'atlas_sha256':config['atlas_sha256'],'star_counts':config['qa']['star_counts']}))
if __name__=='__main__':build()
