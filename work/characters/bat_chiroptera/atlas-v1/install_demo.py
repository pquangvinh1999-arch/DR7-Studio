"""Admit the reviewed Bat demo, keeping final Owner animation approval pending."""
from pathlib import Path
import json,hashlib,shutil,copy,sys,importlib.util
from datetime import datetime,timezone
from PIL import Image
import numpy as np
W=Path(__file__).resolve().parent;R=W.parents[3];S=W/'stage';A=R/'assets/bat_chiroptera'
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'plan.json');m=read(S/'clips/animation-clips.json');meta=read(S/'godot_bundle/engine-export.json');roster=read(R/'assets/roster.json');reference=next(c for c in roster['characters'] if c['character_id']=='pteranodon')
body=list(plan['body_actions']);contract=copy.deepcopy(reference['render_contract'])
contract['projectile']['origin_canvas_px']=[225,165];contract['fx_pivot_px']=[176,141]
contract['projectile']['palette']='purple';contract['locomotion']['cycle_order']=list(range(8))
meta['source']['path']='../clips/animation-clips.json';meta['render_contract']=contract
meta['provenance']={'art_source':'host_image','body_method':'imagegen_complete_body_keyframes','canonical_identity':plan['master'],'canonical_identity_sha256':plan['master_sha256'],'motion_reference':'pteranodon','body_part_cut_warp':False,'owner_approved':False,'atlas_demo_only':True,'fx_method':'Existing seven sonic phase silhouettes; hue sampled from imagegen purple variant, palette substitution then uniform0.8scale','fx_evidence':'work/characters/bat_chiroptera/atlas-v1/fx-source-evidence.json'}
write(S/'godot_bundle/engine-export.json',meta);digest=sha(S/'godot_bundle/godot/bat_chiroptera-atlas-00.png')
ims={n:[Image.open(S/'clips'/m['frames'][i]['file']).convert('RGBA') for i in c['frames']] for n,c in m['clips'].items()}
def at(ticks,t):
    for i,d in enumerate(ticks):
        if t<d:return i
        t-=d
    return len(ticks)-1
union=np.zeros((256,384),bool)
for n in body:
    for im in ims[n]:union|=np.array(im)[:,:,3]>0
composite=[];trace=[];release=sum(m['clips']['power_up']['ticks'][:2])
for t in range(sum(m['clips']['power_up']['ticks'])):
    bi=at(m['clips']['power_up']['ticks'],t);im=ims['power_up'][bi].copy();fi=None
    if release<=t<release+14:
        fi=at(m['clips']['sonic_screech_fx']['ticks'],t-release);im.alpha_composite(ims['sonic_screech_fx'][fi],tuple(contract['projectile']['origin_canvas_px'][i]-contract['fx_pivot_px'][i] for i in range(2)))
    union|=np.array(im)[:,:,3]>0;composite.append(im);trace.append({'tick':t,'body_frame':bi,'fx_frame':fi,'origin':contract['projectile']['origin_canvas_px'] if fi is not None else None})
spec=importlib.util.spec_from_file_location('rv',R/'work/characters/t_rex/sharpness-repair/restore_frames.py');rv=importlib.util.module_from_spec(spec);spec.loader.exec_module(rv);rv.WORK=W
samples=[0,5,10,12,14,16,18,20,22,24,29,34,39];sample_ticks=[b-a for a,b in zip(samples,samples[1:]+[40])];rv.review('power_up-composite',[composite[t] for t in samples],sample_ticks);write(W/'verification/composite-sample-ticks.json',{'sample_at_tick':samples,'hold_ticks':sample_ticks});write(W/'verification/power40tick-trace.json',trace)
for bg in ['light','dark','checker']:
    pics=[]
    from PIL import ImageDraw
    for im in composite:
        back=Image.new('RGBA',(384,256),'#eee8dc' if bg=='light' else '#171b23')
        if bg=='checker':
            d=ImageDraw.Draw(back)
            for y in range(0,256,8):
                for x in range(0,384,8):d.rectangle((x,y,x+7,y+7),fill='#aaa' if (x//8+y//8)%2 else '#ddd')
        back.alpha_composite(im);pics.append(back.resize((768,512),Image.Resampling.NEAREST))
    pics[0].save(W/f'review/playback-power_up-composite-{bg}.webp',save_all=True,append_images=pics[1:],duration=[round((i+1)*1000/60)-round(i*1000/60) for i in range(len(pics))],loop=0,lossless=True)
y,x=np.where(union);full={'x':int(x.min()),'y':int(y.min()),'w':int(x.max()-x.min()+1),'h':int(y.max()-y.min()+1)}
sys.path.insert(0,str(R/'tools/art'));from measure_pixel_sharpness import measure
metrics=measure(S/'clips'/m['frames'][m['clips']['idle']['frames'][0]]['file']);write(W/'measurements.json',metrics)
b=metrics['body_bbox_px'];mm={'canvas_size_px':[384,256],'foot_anchor_px':[176,200],'body_only_bbox_px':dict(zip(['x','y','w','h'],b)),'full_fx_bbox_px':full,'reference_ppu_64':64,'world_size_at_64ppu_m':{'body_w_m':round(b[2]/64,3),'body_h_m':round(b[3]/64,3),'aura_w_m':round(full['w']/64,3),'aura_h_m':round(full['h']/64,3)},'tile_32px_span':{'body_tiles_w':b[2]/32,'body_tiles_h':b[3]/32,'full_fx_tiles_w':full['w']/32,'full_fx_tiles_h':full['h']/32}}
review=read(W/'review/keyframe-review.json');assert review['status']=='reviewed_pending_owner';review.update(atlas_sha256=digest,method='imagegen_complete_body_keyframes',owner_approved=False,naturalness_verdict='pending_owner_human_test');write(W/'review/keyframe-review.json',review)
ch=copy.deepcopy(reference)
for k in ['owner_animation_approval','size_transform_reference']:ch.pop(k,None)
ch.update(character_id='bat_chiroptera',display_name='Bat - Chiroptera',role_label='Fierce Bat — Flight / Bite / Purple Sonic Screech',tags=['bat','chiroptera','flying','pixel_art','purple_sonic_wave'],status='finalized_engine_verified_demo_pending_owner',atlas_stage='demo_pending_owner',owner_animation_approval='pending',canonical_identity={'path':plan['master'],'sha256':plan['master_sha256']},map_sync_metrics=mm,render_contract=contract,motion_quality=review,qa_report='docs/characters/bat-chiroptera-atlas-v1-qa.json')
ch['facing_contract']['camera_view']='side_view_2d_three_quarter_same_as_pteranodon';ch['facing_contract']['locomotion_vector_rule']='Aerial flight; hover/cruise/fast flight from complete Bat wingbeat poses matching Pteranodon phases. Short-muzzle bite toward+X; purple sonic wave from mouth.'
ch['facing_contract']['left_facing_rule']='Same direction selection as Pteranodon: whole-sprite horizontal mirror for left-facing set. No turn clip or simulated spin.'
ch['not_applicable_clips']={n:('Owner requested identical Pteranodon scope; '+('guard/win excluded project-wide.' if n in ['guard','win'] else 'No jump, heavy attack or Ki aura in reference set.')) for n in ch['missing_provisional_clips']}
ch['pixel_sharpness_metrics']={'texel_scale_ratio':'Native1px gameplay, Nearest whole-pose registration','edge_acutance_sobel':metrics['edge_acutance_sobel'],'alpha_hardness_pct':100,'visible_alpha_hardness_pct':100,'opaque_key_px':0,'enclosed_key_pockets':0,'outer_ring_spill_fraction':0.0,'reference_note':'Native generated transparency, alpha threshold128; no chroma-key color used. No Sobel forcing or body palette/sharpening.'}
ch['modes']={'combined_1layer':{'label':'Combined1Layer Bat + independent purple sonic FX','godot_prefab':'res://scenes/BatChiroptera.tscn','bundle_id':'bat_chiroptera'}}
assert not A.exists(),'First admission only'
for folder in ['clips','godot_bundle']:shutil.copytree(S/folder,A/folder)
(A/'clips/.gdignore').touch();(A/'source').mkdir();(A/'source/.gdignore').touch()
roster['characters'].insert(0,ch);write(R/'assets/roster.json',roster)
prefab=(R/'scenes/Pteranodon.tscn').read_text().replace('pteranodon','bat_chiroptera').replace('Pteranodon','BatChiroptera').replace('offset = Vector2(-92.0, -200.0)','offset = Vector2(-127.0, -176.0)');(R/'scenes/BatChiroptera.tscn').write_text(prefab)
fx=(R/'scenes/PteranodonSonicWaveFX.tscn').read_text().replace('pteranodon','bat_chiroptera').replace('Pteranodon','BatChiroptera');(R/'scenes/BatChiropteraSonicWaveFX.tscn').write_text(fx)
write(R/ch['qa_report'],{'character_id':'bat_chiroptera','status':'technical_checks_pending','atlas_sha256':digest,'atlas':meta['atlas'],'frames':len(m['frames']),'clips':len(m['clips']),'map_sync_metrics':mm,'render_contract':contract,'motion_quality':review,'technical_checks':'pending','owner_approved':False})
state=read(R/'state.json');now=datetime.now(timezone.utc).isoformat();old=(R/'VERSION').read_text().strip();new='0.10.0'
state['updated_at']=now;state['project']['version']=new;state['project']['version_history'].append({'version':new,'date':now,'summary':'Bat - Chiroptera demo: Pteranodon-equivalent animation set with purple sonic wave; Owner Human Test pending.'});state['current_focus'].update(status='bat_installed_pending_engine_checks',qa_report=ch['qa_report'],preview_url='http://localhost:8080/?character=bat_chiroptera&clip=power_up');write(R/'state.json',state);(R/'VERSION').write_text(new+'\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
    p=R/f;p.write_text(p.read_text().replace(old,new))
protected=read(W/'protected-peers.json');changed=[p for p,h in protected.items() if p!='assets/roster.json' and sha(R/p)!=h];assert not changed,changed
print(json.dumps({'atlas_sha256':digest,'full_fx':full,'runtime_peers_unchanged':len(protected)-1}))
