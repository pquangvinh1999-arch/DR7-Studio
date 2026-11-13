"""Record executed QA evidence; never grants Owner motion approval."""
from pathlib import Path
import json,datetime,hashlib,shutil
R=Path(__file__).resolve().parents[4];W=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=read(W/'protected-peers.json');assert all(sha(R/p)==h for p,h in protected.items())
browser=read(W/'verification/browser-all-poses.json');assert not browser['errors'];assert len(browser['results'])==21
for v in browser['results']:
 n={'idle':12,'walk':8,'attack_nomal':8,'power_up':9,'hit':6,'ko':8,'turn':4}[v['clip']];assert v['order']==list(range(n))+([0] if v['clip'] in ['idle','walk'] else []),v
proof=read(W/'verification/alpha-key-proof.json');assert all(x['opaque_key_px']==0 and x['enclosed_key_pockets']==0 for x in proof)
assert all(x['outer_ring_spill_fraction']==0 for x in proof if x['outer_ring_spill_fraction'] is not None)
assert all(x['alpha_hardness_pct']==100 for x in proof if x['outer_ring_spill_fraction'] is None)
write(W/'verification/peer-proof.json',{'protected_files':len(protected),'unchanged':True,'characters':['t_rex','spinosaurus','pteranodon','tasmanian_king_crab']})
for a,b in [('test','loop-test'),('import','godot-import'),('wasm','wasm-build'),('clips','clips-build'),('export','engine-export')]:shutil.copyfile('/tmp/dr7-sarco-'+a+'.log',W/'verification'/f'{b}.log')
p=W/'review/keyframe-review.json';v=read(p);v['filmstrips_opened']=['idle','walk','attack_nomal','power_up','hit','ko','turn','energy_blast_fx','energy_charge_fx','power_up-composite'];v['composite_review']='Opened light/dark/checker; mouth points measured in mouth-grid.png:0[237,202],1[239,190],release2[244,194].';v['motion_at_real_time']='Chromium Rust WASM runtime traversed all7bodyclips on all3backgrounds at1x playback; exact forward order and idle/walk seam recorded. Naturalness remains Owner pending.';v['limitations']='Frame strips and runtime stills reviewed directly; browser timing traces verify playback order, not a human naturalness verdict.';write(p,v)
q=R/'docs/characters/sarcosuchus-atlas-v1-qa.json';qa=read(q);qa['status']='technical_verified_pending_owner';qa['technical_checks']={'loop_test_exit_code':0,'python_e2e_tests':35,'godot_bundles':5,'godot_power_tick_test_exit_code':0,'rust_tests':2,'wasm_release_build_exit_code':0,'browser_page_errors':[],'browser_sequences':21,'HTTP_atlas_tres_meta_WASM_byte_parity':True,'standalone_godot_bundle_and_power_tests_exit_code':0};qa['atlas']['pages'][0]['cells']=61;qa['clip_frame_references']=63;qa['protected_peer_files']=len(protected);qa['preview_url']='http://localhost:8080/?character=sarcosuchus&clip=power_up&frame=0&paused=1';qa['warnings']=['Sarcosuchus excluded by Owner: run,jump,guard,attack_heavy,aura_loop,win; attack_light is absent because normal bite uses Owner ID attack_nomal.','motion=reviewed_pending_owner; Owner Human Test chưa nghiệm thu.','Existing ISS-TREX-TICK-LEGACY remains out of scope; no approved peer assets changed.'];qa['fx_cleanup']={'before_example':{'file':'energy_blast_00.png','canvas_px':[172,113],'RGBA':[9,121,48,218],'edge_green_pixels':61,'edge_pixels':87},'after_evidence':'work/characters/sarcosuchus/atlas-v1/verification/alpha-key-proof.json','method':'Green-key foreground bound G<=max(R,B) for source blue/white FX; alpha solve and unmix all contaminated pixels. No AI redraw.'};write(q,qa)
preview=qa['preview_url'];now=datetime.datetime.now(datetime.timezone.utc).isoformat();s=read(R/'state.json');s['updated_at']=now;s['current_focus'].update(status='ready_for_owner_human_test',summary='Sarcosuchus demo v0.8.0:7bodyactions55poses,9clips/62PNG/61atlas_cells/63refs, atlas3106x2082,master157x34. attack_nomal jaw bite;6sourceFXleft→right once,mouth release body2/tick10,hide28. loop35Python/E2E+5Godotbundle+2power-tests+2Rust exit0,WASM0,Chromium21sequences0errors,HTTP/ZIPparity.716peerfiles unchanged. Owner atlas Human Test pending; noPIPE005/no push.',preview_url=preview,qa_report='docs/characters/sarcosuchus-atlas-v1-qa.json');write(R/'state.json',s)
p=W/'plan.json';v=read(p);v['status']='technical_verified_pending_owner';write(p,v)
(R/'docs/characters/sarcosuchus-atlas-v1-qa.md').write_text('''# Sarcosuchus atlas demo v0.8.0

Master approved separately; atlas motion remains pending Owner Human Test.

- Body: idle12, walk8, attack_nomal8, power_up9, hit6, ko8, turn4 (55 poses). No run/jump/heavy/aura/guard/win.
- Whole-body imagegen poses from the approved master; no limb cut/warp/patch. Original idle0/turn0 retained exactly. Four perspective turn poses are used for A/D facing changes,20ticks.
- Power source: immutable `image copy.png`,690×159, six poses left-to-right. Pocket-first green key and contamination unmix; no FX redraw. One scaled source-sphere variant supplies the small charging sphere.
- Release from mouth at bodyframe2/tick10; sixFX×3ticks once; hidden at tick28. Charge anchors Canvas(237,202)/(239,190), release(244,194); projectile velocity(4,0)px/tick.
- One atlas3106×2082,61cells,62sourcePNG,63clipreferences; Nearest60Hz exact integer ticks. Canvas384×256,anchor176,224; idle body157×34,2.453×0.531m at64PPU. Measured idle Sobel254.471, hard body alpha100%; no scalar forcing.
- Technical: loop.sh test exit0,35Python/E2E,5Godotbundles,both charge tests,2Rusttests; WASMrelease exit0. Browser traversed21action/background sequences with0pageerrors; HTTP byte/hash parity and extracted GodotZIP tests exit0.716approved peer files unchanged.
- Motion: filmstrips/composite on light,dark,checker and runtime stills opened directly. Playback traces verify frame traversal and loop seams; naturalness requires Owner review. Technical results do not certify natural gait or bite feel.
- WARN: Owner-excluded reference clips remain reported; normal bite is named attack_nomal. Existing T-rex legacy tick issue is unchanged and outside this task.

Preview: '''+preview+'\n\nDetailed measured data and evidence: [QA JSON](sarcosuchus-atlas-v1-qa.json). No atlas approval receipt, PIPE005 or push has been created.\n')
print(json.dumps({'status':qa['status'],'preview_url':preview,'peer_files_unchanged':len(protected)}))
