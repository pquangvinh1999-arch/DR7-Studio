"""Freeze Bat master and prepare Pteranodon motion-only references."""
from pathlib import Path
import json, hashlib, shutil
from datetime import datetime, timezone
from PIL import Image
W=Path(__file__).resolve().parent;R=W.parents[3]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for d in ['generated','guides','prompts','source','stage','review','verification']: (W/d).mkdir(parents=True,exist_ok=True)
master=R/'work/characters/bat_chiroptera/demo-v1/master.png'
approved=W.parent/'approved-master';approved.mkdir(exist_ok=True)
shutil.copy2(master,approved/'master.png')
write(approved/'approval.json',{'status':'owner_authorized_animation_from_shown_master','owner_message':'anh muốn bat họa tảnh giống hệt dực long. nhưng sóng âm chuyển sang màu tím','scope':'Continue shown Bat identity into Pteranodon-equivalent animation set; final animation Human Test pending.','sha256':sha(master)})
im=Image.open(master).convert('RGBA');crop=im.crop(im.getbbox());guide=Image.new('RGBA',(768,512));guide.alpha_composite(crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST),(132,100));guide.save(W/'guides/bat-identity.png')
src=R/'assets/pteranodon/clips';m=json.loads((src/'animation-clips.json').read_text());s=json.loads((src/'source-manifest.json').read_text())
write(W/'source/pteranodon-animation-clips.json',m);write(W/'source/pteranodon-source-manifest.json',s)
actions={n:len(c['frames']) for n,c in m['clips'].items() if n!='sonic_screech_fx'}
for n,c in m['clips'].items():
    sheet=Image.new('RGBA',(1536,1024))
    for i,idx in enumerate(c['frames']):
        im=Image.open(src/m['frames'][idx]['file']).convert('RGBA')
        if n=='sonic_screech_fx':
            # FX only, 4x integer guide; each phase retains its source canvas coordinates.
            b=im.getbbox();tile=im.crop(b);tile=tile.resize((tile.width*4,tile.height*4),Image.Resampling.NEAREST)
            sheet.alpha_composite(tile,((i%4)*384+192-tile.width//2,(i//4)*512+256-tile.height//2))
        else:
            # Whole source frame only; same uniform1.6 scale and root for all poses.
            tile=im.resize((614,410),Image.Resampling.NEAREST)
            cell=Image.new('RGBA',(384,512));cell.alpha_composite(tile,(-90,30));sheet.alpha_composite(cell,((i%4)*384,(i//4)*512))
    sheet.save(W/f'guides/{n}-motion.png')
plan={'character_id':'bat_chiroptera','display_name':'Bat - Chiroptera','master':str((approved/'master.png').relative_to(R)),'master_sha256':sha(master),'body_actions':actions,'ticks':{n:c['ticks'] for n,c in m['clips'].items()},'reference':'pteranodon','reference_motion_sha256':sha(src/'animation-clips.json'),'scope':'Same clips/framecounts/order/ticks/events as Pteranodon; new complete Bat poses, purple sonic FX.','camera':'Same 3/4 right-facing view as approved Pteranodon','size':'Rest wingspan126px vs Pteranodon157px (rounded80%)','canvas_size_px':[384,256],'anchor_px':[176,200],'source_grid':[4,2],'art_source':'host_image','method':'imagegen_complete_body_keyframes','owner_animation_approved':False}
write(W/'plan.json',plan)
shutil.copy2(W.parent/'demo-v1/protected-peers.json',W/'protected-peers.json')
state=json.loads((R/'state.json').read_text());state['updated_at']=datetime.now(timezone.utc).isoformat();state['current_focus'].update(active_task_id='TASK-065',status='generating_bat_complete_body_actions',summary='Owner requests Bat animation set identical to Pteranodon, purple sonic wave. Freeze shown126x81master;7bodyactions/54newcompleteposes+7FXphases,timing inherited; finalHumanTestpending.',atlas_plan=str((W/'plan.json').relative_to(R)));write(R/'state.json',state)
print(json.dumps(plan,indent=2))
