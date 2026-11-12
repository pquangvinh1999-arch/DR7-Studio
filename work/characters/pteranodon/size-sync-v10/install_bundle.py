"""Install the verified size-only derivative, keeping prior approval provenance."""
import copy,datetime,hashlib,json,pathlib,shutil,sys
from PIL import Image
import numpy as np
WORK=pathlib.Path(__file__).resolve().parent;ROOT=WORK.parents[3];STAGE=WORK/'stage';SRC=WORK/'source';ASSET=ROOT/'assets/pteranodon'
sys.path.insert(0,str(ROOT/'tools/art'));from measure_pixel_sharpness import measure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
protected=read(WORK/'protected-peers.json');assert all(sha(ROOT/p)==v for p,v in protected.items())
m=read(STAGE/'clips/animation-clips.json');meta=read(STAGE/'godot_bundle/engine-export.json');transform=read(WORK/'transform.json');digest=sha(STAGE/'godot_bundle/godot/pteranodon-atlas-00.png');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
records=[dict(clip=name,position=pos,**measure(STAGE/'clips'/m['frames'][i]['file'])) for name,c in m['clips'].items() for pos,i in enumerate(c['frames'])];write(WORK/'measurements.json',records)
oldroster=read(ROOT/'assets/roster.json');ch=next(c for c in oldroster['characters'] if c['character_id']=='pteranodon');motion=copy.deepcopy(ch['motion_quality']);motion.update(atlas_sha256=digest,previous_revision_atlas_sha256=transform['source_atlas_sha256'],review_evidence='work/characters/pteranodon/size-sync-v10/review/keyframe-review.json',owner_feedback='Owner approved157x107 size sample and explicitly requested applying it to the whole bundle. Actions and timing inherit the previously approved source; no new motion authored.',size_transform_authorized=True)
motion['approval_scope']='Previously approved motion + explicitly approved fixed size transform. Not a newly authored motion review.'
ch['motion_quality']=motion;ch['qa_report']='docs/characters/pteranodon-size-sync-v10-qa.json';ch['render_contract']=meta['render_contract'];ch['size_transform_reference']='work/characters/pteranodon/size-sync-v10/transform.json'
body=next(v for v in records if v['clip']=='idle' and v['position']==0)['body_bbox_px'];assert body[2:]==[157,107]
union=np.zeros((256,384),bool)
for f in m['frames']:union|=np.array(Image.open(STAGE/'clips'/f['file']))[:,:,3]>0
# Include all emitted FX composites at their actual new mouth origin.
power=m['clips']['power_up'];fx=m['clips']['sonic_screech_fx'];rc=meta['render_contract'];delta=tuple(a-b for a,b in zip(rc['projectile']['origin_canvas_px'],rc['fx_pivot_px']))
for pos,i in enumerate(power['frames']):
 im=Image.open(STAGE/'clips'/m['frames'][i]['file']).convert('RGBA');elapsed=sum(power['ticks'][2:pos]);end=0
 if pos>=2 and elapsed<rc['projectile']['lifetime_ticks']:
  for fi,t in zip(fx['frames'],fx['ticks']):
   end+=t
   if elapsed<end:im.alpha_composite(Image.open(STAGE/'clips'/m['frames'][fi]['file']).convert('RGBA'),delta);break
 union|=np.array(im)[:,:,3]>0
ys,xs=np.where(union);full=dict(x=int(xs.min()),y=int(ys.min()),w=int(xs.max()-xs.min()+1),h=int(ys.max()-ys.min()+1))
mm=ch['map_sync_metrics'];mm['body_only_bbox_px']=dict(zip(['x','y','w','h'],body));mm['full_fx_bbox_px']=full;mm['reference_ppu_64']=64
for label,b in [('body',mm['body_only_bbox_px']),('aura',full)]:
 for axis in ['w','h']:mm['world_size_at_64ppu_m'][f'{label}_{axis}_m']=round(b[axis]/64,3)
for label,b in [('body',mm['body_only_bbox_px']),('full_fx',full)]:
 for axis in ['w','h']:mm['tile_32px_span'][f'{label}_tiles_{axis}']=round(b[axis]/32,3)
ch['pixel_sharpness_metrics'].update(texel_scale_ratio='Fixed whole-frame nearest size transform from approved source; gameplay detail pitch1px',edge_acutance_sobel=records[0]['edge_acutance_sobel'],alpha_hardness_pct=min(r['alpha_hardness_pct'] for r in records))
receipt=read(SRC/'owner_approval.json');receipt.update(approved_at=now,approved_revision='size-sync-v10',owner_message='ok anh duyệt kích thước này giúp anh đồng bộ bundle sau đó báo cáo lại để anh bắt đầu đưa ra yêu cầu cho atlas của tasmanian',atlas_sha256=digest,qa_report=ch['qa_report'],release_version='0.6.1',approval_scope='Owner approved the157x107 size sample and authorized deterministic size-only application to all existing body/FX frames. Source motion remains previously approved.',source_approval_receipt='work/characters/pteranodon/size-sync-v10/source/owner_approval.json',source_atlas_sha256=transform['source_atlas_sha256'],body_only_bbox_px=mm['body_only_bbox_px'],size_transform=ch['size_transform_reference'])
ch['owner_animation_approval'].update(approved_at=now,atlas_sha256=digest,approval_file='assets/pteranodon/owner_approval.json')
meta['provenance'].update(owner_approved=True,owner_animation_approved=True,atlas_demo_only=False,release_version='0.6.1');write(STAGE/'godot_bundle/engine-export.json',meta)
for folder in ['clips','godot_bundle']:
 target=ASSET/folder
 for sidecar in target.rglob('*.import'):
  dst=STAGE/folder/sidecar.relative_to(target);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sidecar,dst)
 shutil.rmtree(target);shutil.copytree(STAGE/folder,target)
(ASSET/'clips/.gdignore').touch();write(ASSET/'owner_approval.json',receipt);write(ROOT/'assets/roster.json',oldroster)
# Prefab FX pivot and origin must match the very same contract used by localhost.
p=ROOT/'scenes/PteranodonSonicWaveFX.tscn';p.write_text(p.read_text().replace('offset = Vector2(-176.0, -128.0)','offset = Vector2(-176.0, -141.0)'))
p=ROOT/'scenes/Pteranodon.tscn';p.write_text(p.read_text().replace('offset = Vector2(-74.0, -200.0)','offset = Vector2(-92.0, -200.0)'))
write(WORK/'review/keyframe-review.json',dict(status='owner_approved',atlas_sha256=digest,owner_approved=True,scope=motion['approval_scope'],filmstrip_review='Opened all8clip filmstrips+power_up-composite, each on light/dark/checker; source poses retained by the same global map.',motion_method='No motion design or timing changes. Existing Owner motion approval is inherited; scale authorization recorded separately.',visual_runtime_review='Pending observation at real-time; generated playback files preserve the original ticks.',artifacts={p.name:sha(p) for p in (WORK/'review').glob('*') if p.suffix in ['.png','.webp']}))
write(ROOT/ch['qa_report'],dict(character_id='pteranodon',status='size_sync_installed_pending_technical_checks',atlas_sha256=digest,atlas=meta['atlas'],body_only_bbox_px=mm['body_only_bbox_px'],full_fx_bbox_px=full,frames=61,body_frames=54,fx_frames=7,clips=8,canvas_size_px=[384,256],anchor_px=[176,200],motion_quality=motion,metadata_preserved=True,sample_rgba_exact=True,measurements='work/characters/pteranodon/size-sync-v10/measurements.json',transform=ch['size_transform_reference'],render_contract=rc,protected_peer_files=len(protected),technical_checks='pending'))
# Freeze Tasmanian's approved-size input, not an invented one-frame character bundle.
crab=ROOT/'work/characters/tasmanian_king_crab/size-master';crab.mkdir(exist_ok=True);shutil.copyfile(ROOT/'work/reviews/character-size-v1/tasmanian_king_crab-sample.png',crab/'master.png');(crab/'.gdignore').touch();write(crab/'master.json',dict(schema='dr7-studio.size_locked_master.v1',character_id='tasmanian_king_crab',status='owner_size_approved_actions_pending',owner_approved_size=[133,64],canvas_size_px=[384,256],foot_anchor_px=[176,224],sampling='nearest',alpha_hardness_pct=100,master_sha256=sha(crab/'master.png'),source='work/reviews/character-size-v1/tasmanian_king_crab-sample.png',size_reference='Spinosaurus idle0 width157px;0.85*157=133.45 rounded133',atlas_status='not_created_waiting_owner_action_requirements'))
s=read(ROOT/'state.json');s['updated_at']=now;s['project']['version']='0.6.1';s['project']['version_history'].append(dict(version='0.6.1',date=now,summary='Áp kích thước Pteranodon157x107 vào toàn bộ61frame/bundle/FX, giữtiming; khóa Tasmanian133x64 làm đầu vào chờ yêu cầu atlas.'))
w=next(x for x in s['approved_workflows'] if x['character_id']=='pteranodon');w.update(approved_at=now,approval_file='assets/pteranodon/owner_approval.json',atlas_sha256=digest);w.pop('approved_atlas_path',None)
s['current_focus']=dict(active_task_id='TASK-056',status='installed_pending_verification',summary='ĐãcàibundlePtera size-sync-v10,61frames/8clips;idle0byteexactmẫu157x107. FXorigin260141/pivot176141,prefabđồngbộ. ĐãkhóaTasmanian133x64master,chưaatlas. ChờkiểmGodot/Rust/WASM/HTTP.')
write(ROOT/'state.json',s);(ROOT/'VERSION').write_text('0.6.1\n')
for f in ['project.godot','engines/rust_combat_sim/Cargo.toml','engines/rust_combat_sim/Cargo.lock']:
 p=ROOT/f;p.write_text(p.read_text().replace('0.6.0','0.6.1'))
# Size-approved workflow update only; no new Tasmanian workflow is asserted.
p=ROOT/'skills.md';txt=p.read_text();i=txt.index('### [PIPE-002]');j=txt.index('### [PIPE-003]');part=txt[i:j].replace(transform['source_atlas_sha256'],digest);part+='- **Kích thước Owner duyệt và yêu cầu đồng bộ (v0.6.1)**: idle0 157×107px bằng chiều ngang Spino157px. Áp một raster map cố định cho61frame thân/FX; không đổi timing/động tác. FXorigin[260,141],pivot[176,141],anchor thân[176,200]; prefab vàlocalhost dùng cùngcontract. Nguồn/receipt cũ giữ trong work/characters/pteranodon/size-sync-v10/source/,transform vàSHA mới trong QA size-sync-v10. Đây là ủy quyền áp size đãduyệt trênmotion đãduyệt, không phải hoạtảnhmới.\n\n';p.write_text(txt[:i]+part+txt[j:])
assert all(sha(ROOT/p)==v for p,v in protected.items())
print(json.dumps({'atlas_sha256':digest,'body':body,'full_fx':full,'peer_files_unchanged':len(protected)}))
