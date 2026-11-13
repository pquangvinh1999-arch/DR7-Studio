from pathlib import Path
import json,hashlib,shutil,datetime
W=Path(__file__).resolve().parent;R=W.parents[3]
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
browser=read(W/'verification/browser-power-up.json');assert len(browser['ticks'])==46 and len(browser['playback'])==3 and not browser['pageErrors']
for p in ['standalone-import','standalone-bundles','standalone-power']:assert (W/'verification'/f'{p}.log').exists()
base=read(W/'baseline.json');assert all(sha(R/p)==h for p,h in base['protected_peers'].items())
for name in ['clips','export','import','wasm','test','browser']:shutil.copyfile('/tmp/dr7-sarco-v2-'+name+'.log',W/'verification'/f'{name}.log')
q=R/'docs/characters/sarcosuchus-power-up-v2-qa.json';v=read(q);v.update(warnings=[x for x in Path('/tmp/dr7-sarco-v2-test.log').read_text().splitlines() if x.startswith('[WARN]')],status='technical_verified_pending_owner',technical_checks={'loop_test_exit_code':0,'python_e2e_tests':36,'godot_bundles':5,'power_tick_tests':2,'rust_tests':2,'wasm_release_exit_code':0,'browser_ticks_verified':46,'browser_real_time_backgrounds':3,'browser_page_errors':[],'downloaded_godot_pack_tests_exit_code':0,'HTTP_atlas_meta_tres_WASM_byte_parity':True},protected_peer_files_unchanged=len(base['protected_peers']),body_pngs_ticks_events_unchanged=55,owner_feedback='Cầu phải xuất hiện/lớn dần theo hàm mở, vừa miệng, không che răng, phóng với cùng kích thước cuối lúc gồng.',previous_bright_tooth_overlap=[10,24,28],current_bright_tooth_overlap=[0]*11,bright_tooth_test_limits='ROI Canvas[228:253,182:210], RGB thresholds130/120/85 identify bright tooth/jaw pixels; visual review on3backgrounds remains independent.',max_sphere_size_px=[10,9],last_charge_equals_first_projectile_RGBA=True,preview_url='http://localhost:8080/?character=sarcosuchus&clip=power_up&frame=0&paused=1');write(q,v)
p=W/'review/keyframe-review.json';a=read(p);a['real_time']='Chromium Rust WASM body power_up0..8→0 on light/dark/checker; all46ticks layer/frame/point contract checked; screenshots0/4/5/7/9/10/13 reviewed.';a['owner_approved']=False;write(p,a)
p=R/'docs/characters/sarcosuchus-atlas-v1-qa.json';a=read(p);a['status']='superseded_owner_requested_power_up_fix';a['superseded_by']='docs/characters/sarcosuchus-power-up-v2-qa.json';a['owner_feedback']='Power_up sphere covers teeth/opening mouth; revision requested.';a['motion_quality']['checks']['fx_jaw_visibility']=False;a['motion_quality']['unresolved_structural_failures']=['Sphere occluded teeth: measured bright-pixel overlaps10/24/28 atbody0/1/2; corrected only inpower-up-v2.'];write(p,a)
(R/'docs/characters/sarcosuchus-power-up-v2-qa.md').write_text('''# Sarcosuchus power_up v2 — v0.8.1

Cầu hiện/lớn dần theo hàm mở:10tick FX1→10px, alpha32→255; cực đại10×9px. Anchor Canvas(236,201) ở thân0 và(239,193) ở thân1; phóng tại thân2/tick10 ở(244,194). PNG cuối gồng bằng chính xác PNG đầu bay, không tăng cỡ khi phóng. Sáu FX nguồn tiếp tục chạy trái→phải một lượt,ẩn tick28.

55PNG thân,tick/events,7bodyactions và716file của4nhân vật trước giữ nguyênSHA. ChỉresampleFX nguồn đãkey, không AIredraw/thaypose. Bản cũ có10/24/28pixel răng sáng bịphủ ởthân0/1/2; bản mới0pixel qua11mốc0..10, phép đoROI/RGB chỉ hỗ trợ review bằng mắt. Đã mởfilmstrip/composite3nền và runtime screenshots; cảm nhận chuyển động vẫn chờOwner.

Kỹthuật:loop.sh testexit0,36Python/E2E,5Godotbundle,2charge-tests,2Rust;WASMrelease0. Chromium kiểm46tick,phát0..8→0 trên3nền,0pageerrors. HTTPbyteparity vàGodotZIPimport/bundle/power-testexit0. Atlas1page3494×2082,69cell/71PNG/71cliprefs,Nearest60Hz. WARN clipthamchiếuđãloại vàmotionpendingOwner vẫn giữ.

[Demo](http://localhost:8080/?character=sarcosuchus&clip=power_up&frame=0&paused=1). [Số đo/bằng chứng](sarcosuchus-power-up-v2-qa.json). Chưa cóOwneratlasapproval/PIPE005.
''')
p=R/'state.json';s=read(p);s['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['current_focus'].update(status='ready_for_owner_human_test',summary='Sarcosuchus power_up v2 v0.8.1:10charge tickposes1→10px/alpha32→255, max10x9 fits openjaw; bright-tooth overlap0 at0..10vsold10/24/28; finalcharge==launchRGBA. Releasebody2/tick10,6FXonce→hide28.55bodyPNGs/ticks/events +716peerfiles frozen. loop36Python/E2E+5Godotbundles+2charge+2Rust exit0,WASM0,browser46ticks/3backgrounds0errors,HTTP/ZIPparity0. Owner Human Test pending.',qa_report='docs/characters/sarcosuchus-power-up-v2-qa.json',preview_url=v['preview_url']);write(p,s)
print(json.dumps({'status':v['status'],'max_orb_px':[10,9],'body_unchanged':55,'peer_files_unchanged':716}))
