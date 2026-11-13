"""Freeze Owner-accepted Bat atlas without regenerating art or authored timing."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, shutil

R=Path(__file__).resolve().parents[3]
A=R/'assets/bat_chiroptera';W=R/'work/characters/bat_chiroptera/atlas-v1'
F=W.parent/'approved-final-frames'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

assert not (A/'owner_approval.json').exists(),'Never overwrite an Owner approval receipt'
assert not F.exists(),'Never overwrite frozen final frames'
now=datetime.now(timezone.utc).isoformat()
message='ok bat anh chốt luôn tiến hành chốt theo qui trình để qua char tiếp theo'
version=(R/'VERSION').read_text().strip()
atlas=A/'godot_bundle/godot/bat_chiroptera-atlas-00.png'
tres=A/'godot_bundle/godot/bat_chiroptera.tres'
prefab=R/'scenes/BatChiroptera.tscn'
manifest=A/'clips/animation-clips.json'
digest=sha(atlas)
assert digest=='6312e1806453c4879fa683dfbd8f7fec4d180a6b803e0a7d513943c84f01e67a'
peers=read(W/'protected-peers.json');peers.pop('assets/roster.json',None)
assert all(sha(R/p)==h for p,h in peers.items())
before={str(p.relative_to(R)):sha(p) for p in A.rglob('*') if p.is_file() and p.suffix in ['.png','.tres','.tscn']}
for p in [manifest,A/'clips/source-manifest.json',prefab,R/'scenes/BatChiropteraSonicWaveFX.tscn']:
    before[str(p.relative_to(R))]=sha(p)
shutil.copytree(A/'clips',F)
roster=read(R/'assets/roster.json');ch=next(c for c in roster['characters'] if c['character_id']=='bat_chiroptera')
receipt={'schema':'dr7-studio.owner_approval_receipt.v1','status':'owner_approved','workflow_id':'PIPE-007','character_id':'bat_chiroptera','display_name':'Bat - Chiroptera','approved_at':now,'owner_message':message,'approved_revision':'atlas-v1 / v'+version,'release_version':version,'atlas_path':str(atlas.relative_to(R)),'atlas_sha256':digest,'tres_path':str(tres.relative_to(R)),'tres_sha256':sha(tres),'prefab_path':str(prefab.relative_to(R)),'prefab_sha256':sha(prefab),'clips_manifest_path':str(manifest.relative_to(R)),'clips_manifest_sha256':sha(manifest),'canvas_size_px':[384,256],'foot_anchor_px':[176,200],'body_only_bbox_px':ch['map_sync_metrics']['body_only_bbox_px'],'full_fx_bbox_px':ch['map_sync_metrics']['full_fx_bbox_px'],'present_clips':ch['present_clips'],'effect_clips':ch['effect_clips'],'excluded_clips':ch['missing_provisional_clips'],'render_contract':copy.deepcopy(ch['render_contract']),'qa_report':ch['qa_report'],'frozen_source':str((F/'animation-clips.json').relative_to(R)),'approved_runtime_files_sha256':before,'approval_scope':'Owner accepts the shown complete Bat revision: Pteranodon-equivalent actions/timing and purple sonic wave. All images, frame order, ticks, events and FX geometry frozen. New image/timing revisions need new approval.','known_technical_limits':'Five33ms FXpose observations were missed in headless recorded browser playback; offline3background playback observed all61poses. Owner acceptance is not a measured mobile60FPS certification.'}
ch.update(status='finalized_owner_approved',atlas_stage='finalized_owner_approved',owner_animation_approval={'status':'owner_approved','approved_at':now,'approval_file':'assets/bat_chiroptera/owner_approval.json','atlas_sha256':digest})
review=ch['motion_quality'];review.update(status='owner_approved',owner_approved=True,naturalness_verdict='owner_approved',approved_at=now,owner_message=message,limitations='Owner accepted this exact revision. Browser sampling limits remain in QA; no mobile60FPS certification.')
write(R/'assets/roster.json',roster)
meta=read(A/'godot_bundle/engine-export.json');meta['provenance'].update(owner_approved=True,owner_animation_approved=True,atlas_demo_only=False,owner_approval_file='assets/bat_chiroptera/owner_approval.json',approved_at=now,release_version=version);write(A/'godot_bundle/engine-export.json',meta)
receipt['engine_export_path']='assets/bat_chiroptera/godot_bundle/engine-export.json';receipt['engine_export_sha256']=sha(A/'godot_bundle/engine-export.json')
write(A/'owner_approval.json',receipt)
write(F/'freeze-proof.json',{'atlas_sha256':digest,'runtime_files_sha256':before,'approved_at':now,'owner_approval_file':'assets/bat_chiroptera/owner_approval.json'})
write(W/'review/keyframe-review.json',review)
q=read(R/ch['qa_report']);q.update(status='owner_approved',owner_approved=True,approved_at=now,owner_message=message,owner_approval_file='assets/bat_chiroptera/owner_approval.json',motion_quality=copy.deepcopy(review));q['warnings']=[x for x in q['warnings'] if 'bat_chiroptera: motion=' not in x];q['finalization_checks']='pending';write(R/ch['qa_report'],q)
plan=read(W/'plan.json');plan.update(status='finalized_owner_approved',owner_animation_approved=True,owner_approval_file='assets/bat_chiroptera/owner_approval.json',approved_at=now);write(W/'plan.json',plan)
master=read(W.parent/'approved-master/approval.json');master.update(status='owner_approved',approved_at=now,final_character_approval_file='assets/bat_chiroptera/owner_approval.json');write(W.parent/'approved-master/approval.json',master)
entry=f'''### [PIPE-007] Bat - Chiroptera — bộ bay dực long và sóng âm tím
- **Owner nghiệm thu**: `{now}`, atlas-v1 / v{version}. Receipt `assets/bat_chiroptera/owner_approval.json`, atlasSHA `{digest}`; khóa TRES/prefab/manifest/PNG runtime. Bản cuối tại `work/characters/bat_chiroptera/approved-final-frames/`; chỉ copy/repack nguyên frame khi cần xuất lại, không chạy installer demo ghi đè.
- **Nhận diện/kích thước**: masterSHA b8656aaba4eb84dc255f24096d889bcb848fb6cb7af53403476ad10372d7555d, thân/cánh nghỉ126×81px; ngang bằng80% Pteranodon157px sau làm tròn125.6→126. Canvas384×256,anchor[176,200],Nearest,alpha thân100%,chi tiết1px gameplay. Dơi tai lớn,mõm ngắn,nanh nhọn,lông nâu đen,màng cánh đỏ nâu; cùng góc3/4 nhìn phải+X,bay tại chỗ dang cánh như dực long.
- **Bộ hoạt ảnh**: cùng clip/thứ tự/tick/event của Pteranodon; idle8×7tick,walk8×6tick,run8×4tick,attack_light8pose/38tick,power_up8pose/40tick,hit6pose/28tick,ko8pose/52tick. Run là8pose bay nhanh riêng,không dùng lại walk tăng tốc. Vòng0..7→0; không ping-pong. Không jump/heavy/aura/guard/win; giữ WARN tham chiếu kèm lý do. Không thêm turn; mirror chỉ chọn hướng trái/phải giống scope dực long,không giả hoạt ảnh xoay.
- **Phương pháp**: imagegen sinh54pose TOÀN THÂN từ master Bat; dực long chỉ làm motion guide. Không cắt/warp/xoay/ghép chi,cánh hay đầu từ ảnh tĩnh. Tách alpha/crop/register nguyên pose; thân combined_1layer. Master idle0 giữ đúng byte.
- **Sóng âm tím độc lập**:7pha×2tick,phát từ miệng bodyframe2/tick10,lifetime14tick,ẩn tick24;originCanvas[225,165],pivot[176,141],velocity[0,0]. Giữ silhouette/alpha7pha dực long trước thu đồng đều0.8; hue0.772222 lấy từ biến thể tím imagegen,không vẽ lại hình dạng FX. FX thêmquad,cùng trangatlas và contract Godot/localhost.
- **Đóng gói/QA**:61PNG/8clip/1page3106×2082,60Hz;fullFXbbox[106,104,185,129] đo trên gameplay composite. QA `docs/characters/bat-chiroptera-atlas-v1-qa.json`;44Python/E2E+7Godotbundle+4FXtests+2Rust,WASMrelease,ZIPGodotimport/bundle/Batsonic trước chốt đều exit0. Browser24chuỗi/0pageerrors,40tickFXcontract vàHTTPatlas/WASM SHA khớp;5lượtposeFX33ms không được ghi hình headless quan sát,offline3nền đủ61pose. Human Test đã nghiệm thu không thay thế đo60FPS mobile. Giữ master/source/review,PNG staging trùngbyte dọn có mapSHA;revision ảnh/timing mới phải nghiệm thu lại.

'''
p=R/'skills.md';text=p.read_text();assert '[PIPE-007]' not in text;p.write_text(text.replace('<!-- SKILLS_ENTRIES_END -->',entry+'<!-- SKILLS_ENTRIES_END -->'))
# Delete only staging PNG duplicates with a proven retained runtime equivalent.
canonical={h:p for p,h in before.items() if p.endswith('.png')};removed=[]
for p in sorted((W/'stage').rglob('*.png')):
    h=sha(p)
    if h in canonical:
        removed.append({'removed':str(p.relative_to(R)),'retained':canonical[h],'sha256':h,'bytes':p.stat().st_size})
        p.unlink()
write(R/'docs/releases/v0.10.0-bat-finalization.json',{'approved_at':now,'owner_approval_file':'assets/bat_chiroptera/owner_approval.json','atlas_sha256':digest,'runtime_files_frozen':len(before),'peer_files_unchanged':len(peers),'cleanup':{'removed_count':len(removed),'removed_bytes':sum(x['bytes'] for x in removed),'scope':'Only byte-identical stage PNG copies. Master/generated source sheets/review/approved frames preserved. Staging manifests are historical, not rebuild inputs; use frozen final frames.','files':removed},'finalization_checks':'pending'})
s=read(R/'state.json');s['updated_at']=now;s['approved_workflows'].append({'id':'PIPE-007','character_id':'bat_chiroptera','display_name':'Bat - Chiroptera','approved_at':now,'approval_file':'assets/bat_chiroptera/owner_approval.json','atlas_sha256':digest});s['current_focus'].update(active_task_id='TASK-066',status='owner_approved_final_checks',summary='Owner approved Bat atlas-v1/v0.10.0. PIPE007/receipt/frozenframes written without art or timing changes. StagingduplicatePNGcleanup complete; finalengine/paritychecks pending.');s['session_resume'].update(next_action='Hoàn tất kiểm tra chốt Bat, sau đó sẵn sàng nhận nhân vật tiếp theo từ Owner.',asset_status='7 nhân vật Owner-approved: t_rex,spinosaurus,pteranodon,tasmanian_king_crab,sarcosuchus,dilophosaurus,bat_chiroptera.',approval_file='assets/bat_chiroptera/owner_approval.json',review_evidence='work/characters/bat_chiroptera/atlas-v1/review/keyframe-review.json',verification='docs/releases/v0.10.0-bat-finalization.json');write(R/'state.json',s)
p=R/'docs/characters/bat-chiroptera-atlas-v1.md';p.write_text(p.read_text()+f'\nOwner đã nghiệm thu toàn bộ Bat lúc {now}; chốt PIPE-007 và receipt `assets/bat_chiroptera/owner_approval.json`. Nội dung chờ nghiệm thu phía trên là lịch sử trước thời điểm này. Ảnh/timing giữ nguyên; dùng `approved-final-frames/` làm nguồn tái xuất.\n')
assert all(sha(R/p)==h for p,h in before.items())
assert all(sha(R/p)==h for p,h in peers.items())
print(json.dumps({'owner_approved':True,'atlas_sha256':digest,'frozen_runtime_files':len(before),'peer_files_unchanged':len(peers),'removed_duplicate_pngs':len(removed),'removed_bytes':sum(x['bytes'] for x in removed)}))
