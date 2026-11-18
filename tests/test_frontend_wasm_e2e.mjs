import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');
const HTML_PATH = path.join(REPO_ROOT, 'tools/preview/index.html');
const WASM_PATH = path.join(REPO_ROOT, 'tools/preview/rust_combat_sim.wasm');

const html = fs.readFileSync(HTML_PATH, 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, 'index.html must contain inline <script>');
const jsCode = scriptMatch[1];

// 1. Ensure ZERO hardcoded character bundle IDs, Trunks placeholders, or deprecated 3-layer mode in HTML/JS
assert.equal(
  html.toLowerCase().includes('trunks'),
  false,
  'Frontend HTML/JS must NOT contain deleted Trunks placeholders!'
);
assert.equal(
  jsCode.includes('songoku_ssj'),
  false,
  'Frontend JS must NOT reference deleted songoku_ssj bundle IDs!'
);
assert.equal(
  jsCode.includes('layered_3d_depth'),
  false,
  'Frontend JS must NOT contain deprecated layered_3d_depth (Hướng 2) logic!'
);

// 1b. Verify removed Stress Test tab is completely absent from localhost UI
assert.equal(html.includes('tab-stress'), false, 'Frontend HTML/JS must NOT retain removed tab-stress panel');
assert.equal(html.includes('stressCanvas'), false, 'Frontend HTML/JS must NOT retain removed stressCanvas renderer');
assert.equal(jsCode.includes('/api/benchmarks'), false, 'Frontend JS must NOT fetch /api/benchmarks on startup');

// 2. Verify every wasmExports.<fn> call in index.html actually exists in compiled rust_combat_sim.wasm!
const wasmBytes = fs.readFileSync(WASM_PATH);
const wasmMod = await WebAssembly.instantiate(wasmBytes, {});
const realWasmExports = Object.keys(wasmMod.instance.exports);

const calledWasmFns = [...jsCode.matchAll(/wasmExports\.([a-zA-Z0-9_]+)/g)]
  .map(m => m[1])
  .filter(name => name !== 'memory');
for (const fnName of new Set(calledWasmFns)) {
  assert.ok(
    realWasmExports.includes(fnName),
    `JS calls state.wasmExports.${fnName}, which is MISSING from rust_combat_sim.wasm exports: [${realWasmExports.join(', ')}]`
  );
}

// 3. Load real /api/bundles payload directly from Python server module
const apiJsonStr = execFileSync(
  'python3',
  [
    '-c',
    `import json, sys; sys.path.insert(0, 'tools/preview'); import server; b=server.discover_bundles(); print(json.dumps({'bundles': b, 'roster': server.load_finalized_roster(b), 'setups': server.build_setups(b), 'arena_stage': server.load_arena_stage(), 'terrain': server.load_map_terrain(), 'device_profiles': server.load_device_profiles(), 'godot_web_ready': (server.REPO_ROOT / 'build' / 'web' / 'index.html').is_file(), 'android_apk': server.get_android_apk_info(), 'rituals': server.load_rituals(), 'items': server.load_items(), 'parity': server.verify_engine_localhost_parity(), 'review': server.load_review_content()}))`,
  ],
  { cwd: REPO_ROOT, encoding: 'utf8' }
);
const apiPayload = JSON.parse(apiJsonStr);

// 4. Execute the entire frontend application inside a Mock DOM + Canvas2D + WASM VM!
function makeMockCtx2d(canvas) {
  let drawCalls = 0;
  let ellipseCalls = 0;
  return {
    canvas,
    imageSmoothingEnabled: false,
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    font: '',
    filter: 'none',
    get _drawCalls() { return drawCalls; },
    get _ellipseCalls() { return ellipseCalls; },
    clearRect() {},
    fillRect() { drawCalls++; },
    strokeRect() { drawCalls++; },
    beginPath() {},
    rect() {},
    clip() {},
    closePath() {},
    moveTo() {},
    lineTo() {},
    stroke() { drawCalls++; },
    fill() { drawCalls++; },
    ellipse() { ellipseCalls++; drawCalls++; },
    save() {},
    restore() {},
    translate() {},
    scale() {},
    rotate() {},
    setLineDash() {},
    fillText() { drawCalls++; },
    drawImage(img) {
      drawCalls++;
      if (canvas && img && img._mockRgba) canvas._mockRgba = img._mockRgba;
    },
    createLinearGradient() { return { addColorStop() {} }; },
    getImageData(_x, _y, w, h) {
      if (canvas && canvas._mockRgba) return { data: canvas._mockRgba };
      return { data: new Uint8ClampedArray(Math.max(1, w) * Math.max(1, h) * 4) };
    },
    putImageData() {},
  };
}

class MockElement {
  constructor(id = '', tagName = 'DIV') {
    this.id = id;
    this.tagName = tagName;
    this.className = '';
    this._html = '';
    this.textContent = '';
    this.value = '0';
    this.checked = true;
    this.style = { display: '' };
    this.dataset = {};
    this.children = [];
    this.width = 668;
    this.height = 540;
    this._ctx2d = makeMockCtx2d(this);
    this._listeners = {};
    this._attrs = {};
    this.classList = {
      _set: new Set(),
      add: (...c) => c.forEach(x => this.classList._set.add(x)),
      remove: (...c) => c.forEach(x => this.classList._set.delete(x)),
      toggle: (c, force) => {
        const on = force !== undefined ? Boolean(force) : !this.classList._set.has(c);
        if (on) this.classList._set.add(c); else this.classList._set.delete(c);
      },
      contains: c => this.classList._set.has(c),
    };
  }
  get innerHTML() { return this._html; }
  set innerHTML(v) { this._html = String(v); this.children = []; }
  appendChild(ch) { this.children.push(ch); return ch; }
  querySelectorAll() { return []; }
  getContext(kind) {
    if (kind === '2d') return this._ctx2d;
    return null;
  }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.width, height: this.height }; }
  setAttribute(k, v) { this._attrs[String(k)] = String(v); }
  getAttribute(k) { return this._attrs[String(k)] ?? null; }
  addEventListener(ev, fn) { (this._listeners[ev] ||= []).push(fn); }
  click() { if (this.onclick) this.onclick({ preventDefault() {}, target: this }); }
}

const elements = new Map();
const getEl = (id) => {
  if (!elements.has(id)) elements.set(id, new MockElement(id));
  return elements.get(id);
};

const tabHumanBtn = new MockElement('', 'BUTTON'); tabHumanBtn.dataset.tab = 'tab-human';
const tabArenaBtn = new MockElement('', 'BUTTON'); tabArenaBtn.dataset.tab = 'tab-arena';
getEl('btnScale1').dataset.scale = '1';
getEl('btnScale2').dataset.scale = '2';
getEl('btnScale3').dataset.scale = '3';

const sandbox = {
  console,
  WebAssembly,
  Float32Array,
  Uint8ClampedArray,
  Math,
  Number,
  String,
  Boolean,
  Object,
  Array,
  Set,
  Promise,
  Error,
  URLSearchParams,
  performance: { now: () => 1000 },
  setTimeout: () => 1,
  clearTimeout: () => {},
  requestAnimationFrame: () => 1,
  navigator: { clipboard: { writeText: async () => {} } },
  Image: class {
    constructor() { this.naturalWidth = 3890; this.naturalHeight = 3382; }
    set src(_u) { if (this.onload) this.onload(); }
  },
  fetch: async (url) => {
    if (url === '/api/bundles') return { ok: true, json: async () => structuredClone(apiPayload) };
    if (url === '/rust_combat_sim.wasm') {
      return { ok: true, arrayBuffer: async () => wasmBytes.buffer.slice(wasmBytes.byteOffset, wasmBytes.byteOffset + wasmBytes.byteLength) };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  },
  window: { addEventListener() {} },
  document: {
    createElement: (tag) => new MockElement('', tag.toUpperCase()),
    getElementById: (id) => getEl(id),
    querySelector: (sel) => getEl(sel),
    querySelectorAll: (sel) => {
      if (sel === '.tab-btn') return [tabHumanBtn, tabArenaBtn];
      if (sel === '.tab-view') return [getEl('tab-human'), getEl('tab-arena')];
      if (sel === '#arenaScaleControls button[data-scale]') return [getEl('btnScale1'), getEl('btnScale2'), getEl('btnScale3')];
      return [];
    },
  },
};

const instrumentedJs = jsCode + '\n;globalThis.__TEST__ = { sampleShenronSummon, sampleShenronDismiss, applyShenronPixelDissolve, startShenronSummon, startShenronDismiss, chooseShenronWish, renderShenronWishOverlay, dismissShenronSummon, initApp, loadImage, scheduleUiAssetRedraw, buildFilmstrip, renderRosterList, state, arena, selectCharacter, setArenaCharacterScale, updateArenaFrameLayout, stepInspectorAnimation, renderInspector, stepAndRenderArena, triggerArenaAction, toggleArenaPatrol, respawnArenaCharacter, isSidewaysLocked, getCanvasSize, getLayerFramesForStep, selectionPixelRuns, updateAgentSpecText, computeBodyRect, computeEdgeDistance, resetEnemyAiZone, evaluateUtilityAI, selectEnemyCharacter, setUtilityAiEnabled, stepEnemyAiFrame, getPlayerRosterEntry, isAiOnlyMonsterRole, renderArenaControls, getBodyDims, offCtx, sampleItemSparkleFrame, renderDragonBallItemInspector, triggerArenaMonsterDrop, pickupArenaItems, stepArenaItemDrops, syncStaticArenaSampleDrops, computeDeviceLayoutMetrics, applyAndroidApkInfo, getSelectedDeviceProfile, getNearestSupportYBelow, spawnGroundDust };';
vm.createContext(sandbox);
vm.runInContext(instrumentedJs, sandbox);

await new Promise(r => setTimeout(r, 60));
const T = sandbox.__TEST__;

assert.equal(getEl('runtimeErrorBanner').textContent, '', 'initApp must produce ZERO runtime errors');
assert.ok(apiPayload.roster.characters.some(c => c.character_id === 'floating_camera'), 'Floating Camera must be finalized in roster.json');
assert.equal(T.state.api.roster.characters.length, 11, 'Finalized roster must include all 11 approved characters');
T.selectCharacter('floating_camera');
assert.equal(T.state.activeChar.character_id, 'floating_camera', 'Floating Camera must select inside Human Test');
assert.deepEqual(Array.from(T.getBodyDims(T.state.activeChar)), [70, 74], 'Floating Camera body bbox must be 70x74');
assert.equal(T.arena.spawnFacing, 'right', 'Source muzzle faces +X');
assert.equal(T.arena.flyDefaultY, 300, 'Floating Camera must spawn 50px lower than Bat');
assert.equal(T.arena.charScale, 1.0, 'Floating Camera native body is 70x74 at 1x');
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Floating Camera selection must not fail');
{
  // Seamless walk <-> idle continuity when stopping & resuming movement
  T.arena.keys = { KeyD: true };
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.clip, 'walk');
  T.arena.step = 5; T.arena.elapsed = 12;
  T.arena.keys = {};
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.clip, 'idle');
  assert.equal(T.arena.step, 5, 'Floating Camera stopping walk->idle must preserve bobbing frame seamlessly');
  T.arena.keys = { KeyD: true };
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.clip, 'walk');
  assert.equal(T.arena.step, 5, 'Floating Camera resuming idle->walk must preserve bobbing frame seamlessly');
  T.arena.keys = {};

  // Player attack_light launches projectile_fx at release_frame=1
  const attackLayers = T.getLayerFramesForStep('attack_light', 1, { auraEnabled: false });
  assert.ok(Array.isArray(attackLayers) && attackLayers.some(l => l.layer === 'Body'), 'Floating Camera attack_light inspector layers must render without TypeError');
  T.arena.projectiles = [];
  T.triggerArenaAction('attack_light');
  for (let i = 0; i < 20; i++) T.stepAndRenderArena(1000 / 60);
  assert.ok(T.arena.projectiles.some(p => p.clip === 'projectile_fx' && p.owner === 'player'), 'Floating Camera attack_light must launch projectile_fx');
  T.arena.hitstop = 0;
  T.arena.actionClip = null;
  T.arena.projectiles = [];

  // Flying AI without power_up fires attack_light at >=50px
  T.selectEnemyCharacter('floating_camera', true);
  T.setUtilityAiEnabled(true);
  T.arena.enemyAi.x = 1500;
  T.arena.x = 1200;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light', 'Floating Camera AI at >=50px must attack with attack_light');
  T.setUtilityAiEnabled(false);
  T.arena.projectiles = [];
}

// Drum Monster AI + Manual Testability + Player/AI Arena Dropdowns E2E Check
{
  const drumEntry = apiPayload.roster.characters.find(c => c.character_id === 'drum');
  assert.ok(drumEntry, 'Drum must be registered in roster.json');
  const drumBundle = T.state.bundlesById[drumEntry.modes.combined_1layer.bundle_id];
  assert.ok(drumBundle.animations.walk && drumBundle.animations.walk.frames.length === 8, 'Drum must expose 8-frame walk cycle');
  assert.ok(!drumBundle.animations.attack_heavy, 'Drum must NOT expose separate attack_heavy');
  assert.equal(drumBundle.animations.power_up.frames.length, 11, 'Drum power_up must combine Row 3 prep + Row 4-5 (11 frames)');

  // Dropdowns must list playable fighters in selPlayerChar (excluding NPC shenron) & chars in selEnemyChar
  const selPlayer = getEl('selPlayerChar');
  const selEnemy = getEl('selEnemyChar');
  assert.ok(selPlayer && selPlayer.children.some(o => o.value === 'drum'), 'selPlayerChar must list drum for manual testing');
  assert.ok(!selPlayer.children.some(o => o.value === 'shenron'), 'selPlayerChar must exclude NPC shenron');
  assert.ok(selEnemy && selEnemy.children.some(o => o.value === 'drum'), 'selEnemyChar must list drum');

  // Monsters MUST be manually testable on player side; only NPCs (shenron) hide combat skill buttons
  T.selectCharacter('drum');
  assert.equal(T.arena.playerCharId, 'drum', 'Selecting monster drum must allow manual control testing');
  assert.equal(T.arena.charScale, 2.5, 'Drum finalized default scale must be 2.5x');
  assert.equal(drumEntry.render_contract.locomotion.default_scale, 2.5, 'Drum default_scale must be 2.5');
  assert.equal(drumEntry.render_contract.locomotion.screen_speed_px_per_second, 140, 'Drum calibrated screen speed must be 140 px/s');
  assert.equal(drumEntry.render_contract.locomotion.speed_px_per_second, 56.0, 'Drum base speed at 2.5x scale must be 56.0');
  {
    const xBefore = T.arena.x;
    T.arena.keys = { KeyD: true };
    for (let i = 0; i < 30; i++) T.stepAndRenderArena(1000 / 60);
    T.arena.keys = {};
    const moved = T.arena.x - xBefore;
    assert.ok(Math.abs(moved - 70.0) < 1.5, `Drum 0.5s walk displacement must match 140 px/s (~70px), got ${moved}`);
    T.arena.x = xBefore;
  }
  const drumManualBtns = getEl('arenaSkillButtons').children.map(c => c.dataset?.clip).filter(Boolean);
  assert.ok(drumManualBtns.includes('attack_light') && drumManualBtns.includes('power_up'), 'Monster drum must expose physical skill buttons for testing');

  T.selectCharacter('shenron');
  T.renderArenaControls();
  assert.equal(getEl('arenaSkillButtons').children.some(c => c.dataset?.clip), false, 'NPC shenron must not expose manual combat buttons');

  // Switch player to t_rex and enemy AI to drum via quick-switch helpers
  T.selectCharacter('t_rex');
  T.selectEnemyCharacter('drum', true);
  T.setUtilityAiEnabled(true);
  assert.equal(T.arena.enemyAi.charId, 'drum');
  assert.equal(T.arena.playerCharId, 't_rex');

  // Outside zone -> Drum holds stationary idle (never patrols)
  T.arena.x = 560;
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.lastIntent, 'idle');
  assert.equal(T.arena.enemyAi.clip, 'idle');
  assert.equal(T.arena.enemyAi.x, 1360);

  // Enter zone at 50 < edge_dist <= 200 -> teleport (~50px) -> attack_light -> 0.2s continuous attack_light <=50px
  T.arena.enemyAi.x = 1580;
  T.arena.x = 1240; // center gap=340, sum_half=(186*1.75 + 56*2.5)/2=232.75 -> edge_dist=107.25 in (50, 200]
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.actionClip, 'teleport', 'Drum must start teleport in 50..200px band');
  for (let i = 0; i < 16; i++) T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.drumTeleportRelocated, true);
  const [pBw, pBh] = T.getBodyDims(T.getPlayerRosterEntry());
  const [eBw, eBh] = T.getBodyDims(drumEntry);
  const edgeGap = T.computeEdgeDistance(
    T.computeBodyRect(T.arena.enemyAi.x, T.arena.groundY, eBw, eBh, T.arena.enemyScale),
    T.computeBodyRect(T.arena.x, T.arena.groundY, pBw, pBh, T.arena.charScale)
  );
  assert.ok(Math.abs(edgeGap - 50) <= 6, `Drum teleport must stop ~50px edge gap, got ${edgeGap}`);
  assert.equal(T.arena.enemyAi.flip, T.arena.x < T.arena.enemyAi.x, 'Drum must face target after teleport');

  let sawLight = false;
  for (let i = 0; i < 12; i++) {
    T.stepAndRenderArena(1000 / 60);
    if (T.arena.enemyAi.actionClip === 'attack_light') { sawLight = true; break; }
  }
  assert.ok(sawLight, 'Drum must immediately perform Row 2 attack_light after teleport');

  // Wait for first attack_light to finish (~24 ticks) + verify 0.2s cooldown before continuous second strike
  for (let i = 0; i < 28; i++) T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.lastIntent, 'wait_cooldown', 'Drum must honor 0.2s cooldown between continuous attack_light');
  let sawSecondLight = false;
  for (let i = 0; i < 16; i++) {
    T.stepAndRenderArena(1000 / 60);
    if (T.arena.enemyAi.actionClip === 'attack_light') { sawSecondLight = true; break; }
  }
  assert.ok(sawSecondLight, 'Drum <=50px must continuously repeat attack_light every 0.2s');

  // Target retreats outside melee into 200 < edge_dist < 400 -> power_up (11 frames -> orb at frame 10)
  T.arena.enemyAi.actionClip = null;
  T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.enemyAi.x = 1360;
  T.arena.x = 900; // center gap=460, sum_half=(186*1.75 + 56*2.5)/2=232.75 -> edge_dist=227.25 in (200, 400)
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.actionClip, 'power_up', 'Drum in 200<dist<400 must trigger power_up');

  let sawOrb = false;
  for (let i = 0; i < 55; i++) {
    T.stepAndRenderArena(1000 / 60);
    if (T.arena.projectiles.some(p => p.clip === 'electric_orb_fx')) { sawOrb = true; break; }
  }
  assert.ok(sawOrb, 'Drum power_up frame 10 must spawn electric_orb_fx linear projectile');

  // Retreat >= 400px -> stationary idle
  T.arena.enemyAi.actionClip = null;
  T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.x = 700; // edge_dist = 441.25 >= 400
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.enemyAi.lastIntent, 'idle', 'Drum >=400px must revert to stationary idle');

  // Reset cleanly back to initial state
  T.arena.enemyAi.enabled = false;
  T.arena.enemyAi.pinned = false;
  T.arena.projectiles = [];
  T.selectCharacter(apiPayload.roster.characters[0].character_id);
}

// Phase A: Empty Roster (0 characters) verification on real /api/bundles
if (apiPayload.roster.characters.length === 0) {
  assert.equal(T.state.activeChar, null, 'Empty roster must start with activeChar = null');
  assert.equal(getEl('rosterCountBadge').textContent, '0 Hoàn thiện');
  assert.equal(getEl('clipCountBadge').textContent, '0 clips');
  assert.equal(getEl('arenaCharLabel').textContent, 'Chưa có nhân vật');

  tabArenaBtn.click();
  T.stepAndRenderArena(16.67);
  assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 2 Arena with 0 characters must have ZERO runtime errors');
  tabHumanBtn.click();
}

// Real assets use the declared body/effect contract; no deleted-character scenarios.
for (const ch of apiPayload.roster.characters) {
  T.selectCharacter(ch.character_id);
  const bundle=T.state.bundlesById[ch.modes.combined_1layer.bundle_id];
  const contract=bundle.render_contract;
  if (!contract) continue;
  const motion=contract.locomotion?.clip||'idle';
  if (contract.locomotion?.kind === 'stationary') {
    T.arena.x=560; T.arena.y=840; T.arena.vy=-1;
    T.arena.keys={KeyD:true,KeyW:true,Space:true};
    T.arena.customSpeedPxPerSec=999;
    const facing=T.arena.flip;
    T.toggleArenaPatrol();
    const seen=new Set();
    for(let tick=0;tick<100;tick++){T.stepAndRenderArena(1000/60);seen.add(T.arena.step);}
    assert.equal(T.arena.x,560); assert.equal(T.arena.y,840);
    assert.equal(T.arena.flip,facing); assert.equal(T.arena.patrolEnabled,false);
    assert.equal(T.arena.clip,'idle'); assert.equal(seen.size,8);
    T.arena.keys={}; T.arena.customSpeedPxPerSec=null;
  }

  if (contract.aura?.loop_clip && bundle.animations[contract.aura.loop_clip]) {
    const aura=bundle.animations[contract.aura.loop_clip];
    const layers=T.getLayerFramesForStep(motion,0,{auraEnabled:true,fxTicks:0});
    assert.deepEqual(Array.from(layers,x=>x.layer),['Aura','Body']);
    assert.equal(layers[0].frame,aura.frames[0]);
    assert.equal(layers[1].frame,bundle.animations[motion].frames[0]);
  } else {
    const layers=T.getLayerFramesForStep(motion,0,{auraEnabled:true,fxTicks:0});
    assert.deepEqual(Array.from(layers,x=>x.layer),['Body']);
    assert.equal(layers[0].frame,bundle.animations[motion].frames[0]);
  }
  if (contract.projectile?.kind === 'linear_energy') {
    const p = contract.projectile;
    const projLayers = T.getLayerFramesForStep(p.body_clip, p.release_frame, {auraEnabled:false, fxTicks:0});
    assert.deepEqual(Array.from(projLayers, x => x.layer), ['Body', 'Projectile']);
    assert.equal(projLayers[1].frame, bundle.animations[p.projectile_clip].frames[0]);
  }
  if(contract.target_slashes) {
    const q=contract.target_slashes,anim=bundle.animations[q.body_clip];let total=anim.frames.reduce((s,f)=>s+f.duration_ticks,0),visible=0;
    for(let tick=0;tick<total;tick++) {
      let index=0,elapsed=tick;while(index<anim.frames.length-1&&elapsed>=anim.frames[index].duration_ticks){elapsed-=anim.frames[index].duration_ticks;index++;}
      const layers=T.getLayerFramesForStep(q.body_clip,index,{elapsedMs:elapsed*1000/60,auraEnabled:false});
      const strike=q.strikes.find(x=>tick>=x.at_tick&&tick<x.at_tick+x.duration_ticks);
      assert.deepEqual(Array.from(layers,x=>x.layer),strike?['Body','TargetSlash']:['Body']);
      if(strike){visible++;assert.equal(layers[1].frame,bundle.animations[strike.clip].frames[tick-strike.at_tick]);assert.deepEqual(Array.from(layers[1].point),Array.from(q.default_target_canvas_px));
        const custom=T.getLayerFramesForStep(q.body_clip,index,{elapsedMs:elapsed*1000/60,auraEnabled:false,targetCanvasPx:[280,150]});assert.deepEqual(Array.from(custom[1].point),[280,150]);}
    }
    assert.equal(q.strikes.length,3);assert.equal(visible,18);assert.equal(q.active_window_ticks[1]-q.active_window_ticks[0],60);
  }
  if(contract.charge) {
    const q=contract.charge,p=contract.projectile;
    const start=T.getLayerFramesForStep(q.body_clip,0,{elapsedMs:0,auraEnabled:false});
    assert.deepEqual(Array.from(start,x=>x.layer),['Body','Charge']);
    assert.deepEqual(Array.from(start[1].point),Array.from(q.origin_canvas_px_by_frame[0]));
    const body=bundle.animations[q.body_clip],charge=bundle.animations[q.effect_clip];
    const last=q.release_frame-1;
    const lastCharge=T.getLayerFramesForStep(q.body_clip,last,{elapsedMs:(body.frames[last].duration_ticks-1)*1000/60,auraEnabled:false});
    const phaseAt=(frames,tick)=>{let i=0;while(i<frames.length-1 && tick>=frames[i].duration_ticks){tick-=frames[i].duration_ticks;i++;}return i;};
    const release=body.frames.slice(0,q.release_frame).reduce((s,f)=>s+f.duration_ticks,0);
    assert.equal(lastCharge[1].frame,charge.frames[phaseAt(charge.frames,release-1)]);
    for(let elapsed=0;elapsed<p.lifetime_ticks;elapsed++) {
      const bodyElapsed=elapsed*1000/60;
      const layers=T.getLayerFramesForStep(q.body_clip,p.release_frame,{elapsedMs:bodyElapsed,auraEnabled:false});
      assert.deepEqual(Array.from(layers,x=>x.layer),['Body','Projectile']);
      assert.deepEqual(Array.from(layers[1].point),[p.origin_canvas_px[0]+elapsed*p.velocity_px_per_tick[0],p.origin_canvas_px[1]]);
      const projectile=bundle.animations[p.projectile_clip];
      assert.equal(layers[1].frame,projectile.frames[phaseAt(projectile.frames,elapsed)]);
    }
    const gone=T.getLayerFramesForStep(q.body_clip,p.release_frame,{elapsedMs:p.lifetime_ticks*1000/60,auraEnabled:false});
    assert.deepEqual(Array.from(gone,x=>x.layer),['Body']);
  }
  assert.equal(T.getLayerFramesForStep(motion,0,{auraEnabled:false}).length,1);
  if (contract.locomotion?.kind==='ground' && !bundle.animations.run) {
    assert.equal(contract.locomotion.clip,'walk');
    assert.equal(getEl('arenaControlHint').textContent.includes('Shift'),false);
    T.arena.flip=false;T.arena.actionClip=null;T.arena.turnTargetFlip=null;T.arena.hitstop=0;
    T.arena.holdLeft=false;T.arena.holdRight=false;T.arena.keys={KeyD:true};T.arena.x=280;
    T.stepAndRenderArena(1000/60);const plain=T.arena.x-280;
    const x=T.arena.x;T.arena.keys.ShiftLeft=true;T.stepAndRenderArena(1000/60);
    assert.ok(Math.abs(T.arena.x-x-plain)<1e-9,'Shift must keep walk speed when run is excluded');
    assert.equal(T.arena.clip,'walk');T.arena.keys={};
  }
  if (contract.turning?.clip) {
    if (contract.locomotion?.run_pose_source==='independent_generated_run_poses') {
      const walk=bundle.animations.walk,run=bundle.animations.run;
      assert.equal(contract.locomotion.run_uses_walk_frames,false);
      assert.ok(run.frames.some((f,i)=>!walk.frames[i]||f.x!==walk.frames[i].x||f.y!==walk.frames[i].y),'Run must use distinct authored poses');
      if(contract.locomotion.run_step_intervals_ticks){
        const tickAt=i=>run.frames.slice(0,i).reduce((s,f)=>s+f.duration_ticks,0);
        const [a,b]=contract.locomotion.run_contact_frames;const total=run.frames.reduce((s,f)=>s+f.duration_ticks,0);
        assert.deepEqual([tickAt(b)-tickAt(a),total-tickAt(b)+tickAt(a)],[21,21]);
      }
      for(const name of ['walk','run']){
        T.state.activeClipName=name;T.state.stepIdx=0;T.state.stepElapsedMs=0;T.state.playing=true;T.state.speedMult=1;
        const order=[0];const anim=bundle.animations[name];
        const ticks=anim.frames.reduce((s,f)=>s+f.duration_ticks,0);
        for(let t=0;t<ticks*3+2;t++){
          T.stepInspectorAnimation(1000/60);
          if(order.at(-1)!==T.state.stepIdx)order.push(T.state.stepIdx);
        }
        assert.ok(order.length>=anim.frames.length*3,'Must traverse three complete gait cycles');
        order.forEach((index,i)=>assert.equal(index,i%anim.frames.length,'Only forward cyclic playback, including 7→0'));
      }
    }
    for (const clipName of contract.body_clips) {
      const anim=bundle.animations[clipName];
      T.state.activeClipName=clipName; T.state.stepIdx=0; T.state.stepElapsedMs=0;
      T.state.playing=true; T.state.speedMult=1; T.state.autoReplayOneshot=false;
      const seen=new Set([0]);
      const totalMs=anim.frames.reduce((s,f)=>s+f.duration_ms,0);
      for(let ms=0;ms<totalMs+34;ms+=1000/60){
        T.stepInspectorAnimation(1000/60);
        if(!seen.has(T.state.stepIdx)){seen.add(T.state.stepIdx);T.renderInspector();}
      }
      assert.equal(seen.size,anim.frames.length,clipName+' must play every whole pose on the runtime clock');
    }
    T.arena.flip=false; T.arena.keys={KeyA:true}; T.arena.hitstop=0;
    const beforeX=T.arena.x;
    T.stepAndRenderArena(1000/60);
    assert.equal(T.arena.clip,contract.turning.clip);
    assert.equal(T.arena.flip,false,'Keep orientation until perspective poses finish');
    if (ch.character_id === 'chilopoda') {
      assert.equal(T.arena.x,beforeX,'Plant the burrow turn pivot');
    } else {
      assert.ok(Math.abs(T.arena.x - beforeX) <= 15, `${ch.character_id} smooth turnaround momentum stays bounded`);
    }
    T.triggerArenaAction('attack_light');
    assert.equal(T.arena.clip,contract.turning.clip,'Do not interrupt pending orientation');
    const visited=new Set([T.arena.step]);
    for(let i=0;i<contract.turning.duration_ticks+2;i++){T.stepAndRenderArena(1000/60);if(T.arena.clip===contract.turning.clip)visited.add(T.arena.step);}
    assert.deepEqual([...visited],Array.from({length:bundle.animations[contract.turning.clip].frames.length},(_,i)=>i));
    assert.equal(T.arena.flip,true);
    T.arena.keys={KeyD:true};
    T.stepAndRenderArena(1000/60);
    assert.equal(T.arena.clip,contract.turning.clip);
    assert.equal(T.arena.flip,true);
    for(let i=0;i<contract.turning.duration_ticks+2;i++)T.stepAndRenderArena(1000/60);
    assert.equal(T.arena.flip,false);
    T.arena.keys={};
  }
  if (ch.render_contract?.locomotion?.kind === 'flight') {
    const expectedFlightY = Number(ch.render_contract?.locomotion?.flight_default_y ?? 250);
    assert.equal(T.arena.y, expectedFlightY, `${ch.character_id} must spawn at hover altitude Y=${expectedFlightY}`);
    T.arena.keys = { KeyW: true };
    T.stepAndRenderArena(100);
    assert.ok(T.arena.y < expectedFlightY && T.arena.y >= T.arena.flyMinY, `${ch.character_id} KeyW flies upward without gravity snap`);
    const highY = T.arena.y;
    T.arena.keys = { KeyS: true };
    T.stepAndRenderArena(200);
    assert.ok(T.arena.y > highY && T.arena.y <= T.arena.groundY, `${ch.character_id} KeyS flies downward`);
    T.arena.keys = {};
    T.arena.y = expectedFlightY;
  }
  T.renderInspector();
  assert.equal(getEl('runtimeErrorBanner').textContent,'');
}

// Chilopoda's target transfer, delayed hit and endpoint reversal are real runtime behavior.
const chiloCharacter=apiPayload.roster.characters.find(ch=>ch.render_contract?.chilopoda);
if(chiloCharacter){
  T.selectCharacter(chiloCharacter.character_id);
  const b=T.state.bundlesById[chiloCharacter.modes.combined_1layer.bundle_id];
  const c=b.render_contract.chilopoda;
  const layersAt=(clip,tick,options={})=>{
    const a=b.animations[clip];let index=0,left=tick;
    while(index<a.frames.length-1&&left>=a.frames[index].duration_ticks)left-=a.frames[index++].duration_ticks;
    return T.getLayerFramesForStep(clip,index,{elapsedMs:left*1000/60,fxTicks:0,...options});
  };
  let hidden=0;
  for(let tick=0;tick<90;tick++){
    const layers=layersAt('attack_light',tick);const body=layers.find(l=>l.layer==='Body');
    if(tick>=24&&tick<54){hidden++;assert.equal(body,undefined,'Exactly30ticks underground')}
    else assert.ok(body,'Body has an emergence/entry pose outside hidden window');
    if(tick>=54)assert.equal(body.point[0],256,'Root transfers to enemy minus bite contact offset');
  }
  assert.equal(hidden,30);
  for(const initialFacingLeft of [false,true])for(let tick=0;tick<36;tick++){
    const body=layersAt('turn',tick,{initialFacingLeft}).find(l=>l.layer==='Body');
    if(tick>=16&&tick<22)assert.equal(body,undefined,'Turn changes facing only while underground');
    else {assert.ok(body);assert.equal(body.point[0],176,'Burrow turn does not relocate');assert.equal(body.mirror,initialFacingLeft!==(tick>=16));}
  }

  const fbFrames = c.fireball ? b.animations[c.fireball.projectile_clip].frames : [];
  assert.equal(fbFrames.length, 10, 'Single 10-frame fireball_fx progression');
  const charge0 = layersAt('power_up',0).filter(l=>l.layer==='FireballFX');
  const charge15 = layersAt('power_up',15).filter(l=>l.layer==='FireballFX');
  assert.equal(charge0.length, 1); assert.equal(charge15.length, 1);
  assert.ok(fbFrames.indexOf(charge15[0].frame) > fbFrames.indexOf(charge0[0].frame) && fbFrames.indexOf(charge15[0].frame) <= 2, 'Mouth charge condenses across frames 0..2');
  const bolts=layersAt('power_up',16).filter(l=>l.layer==='FireballFX');
  const flight20=layersAt('power_up',20).filter(l=>l.layer==='FireballFX');
  assert.equal(bolts.length,1); assert.equal(flight20.length,1);
  assert.ok(flight20[0].point[0] > bolts[0].point[0], 'Fireball launches toward target');
  assert.ok(fbFrames.indexOf(flight20[0].frame) >= fbFrames.indexOf(bolts[0].frame), 'Fireball grows in flight');
  assert.equal(layersAt('power_up',41).filter(l=>l.layer==='FireballFX').length,0);
  assert.equal(layersAt('power_up',18,{targetGroundCanvasPx:[370,224]}).filter(l=>l.layer==='FireballFX').length,1,'Farther target extends physical flight');
  Object.assign(T.arena,{x:560,flip:false,keys:{},hitstop:0,actionClip:null,turnTargetFlip:null,dummyX:920,dummyHp:2000,popups:[]});
  T.triggerArenaAction('attack_light');assert.equal(T.arena.dummyHp,2000,'No hit before burrow or bite');
  for(let tick=0;tick<92;tick++)T.stepAndRenderArena(1000/60);
  const expectedBiteX = 920 - c.burrow.bite_offset_x_px * T.arena.charScale;
  assert.equal(T.arena.dummyHp,1880);assert.ok(Math.abs(T.arena.x - expectedBiteX) < .001, `Remain at target ${expectedBiteX} after bite, got ${T.arena.x}`);assert.equal(T.arena.clip,'idle');assert.equal(T.arena.chiloPatrol,false);
  Object.assign(T.arena,{x:560,flip:false,keys:{},hitstop:0,actionClip:null,dummyHp:2000,popups:[]});
  T.triggerArenaAction('power_up');assert.equal(T.arena.dummyHp,2000);
  for(let tick=0;tick<44;tick++)T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.dummyHp,1750,'Single 250-damage fireball hit on projectile arrival, not cast start');
  T.selectCharacter(chiloCharacter.character_id);
  Object.assign(T.arena,{x:T.arena.maxX-1,flip:false,keys:{KeyD:true},hitstop:0});
  T.stepAndRenderArena(1000/60);assert.equal(T.arena.clip,'turn');assert.equal(T.arena.flip,false);
  const rightSeen=new Set([T.arena.step]);
  for(let t=0;t<38;t++){T.stepAndRenderArena(1000/60);if(T.arena.clip==='turn')rightSeen.add(T.arena.step)}
  assert.equal(rightSeen.size,b.animations.turn.frames.length);assert.equal(T.arena.flip,true);assert.equal(T.arena.chiloPatrolDir,-1);
  Object.assign(T.arena,{x:T.arena.minX+1,keys:{}});T.stepAndRenderArena(1000/60);assert.equal(T.arena.clip,'turn');assert.equal(T.arena.flip,true);
  const leftSeen=new Set([T.arena.step]);
  for(let t=0;t<38;t++){T.stepAndRenderArena(1000/60);if(T.arena.clip==='turn')leftSeen.add(T.arena.step)}
  assert.equal(leftSeen.size,b.animations.turn.frames.length);assert.equal(T.arena.flip,false);assert.equal(T.arena.chiloPatrolDir,1);
  Object.assign(T.arena,{x:560,flip:false,keys:{},hitstop:0,actionClip:null,turnTargetFlip:null,dummyX:1360,dummyHp:2000,chiloPatrol:false,chiloAction:null});
}

// Two-endpoint walk->turn->walk and run->turn->run transitions + lock mid-turn for retrofitted turn fighters.
for (const turnCharId of ['bat_chiroptera', 't_rex']) {
  const ch = apiPayload.roster.characters.find(c => c.character_id === turnCharId);
  if (!ch) continue;
  T.selectCharacter(ch.character_id);
  const b = T.state.bundlesById[ch.modes.combined_1layer.bundle_id];
  const turnTicks = (ch.render_contract?.turning?.duration_ticks ?? 21) + 4;
  Object.assign(T.arena,{x:T.arena.maxX-1,flip:false,keys:{},hitstop:0,actionClip:null,turnTargetFlip:null,patrolEnabled:false,patrolRun:false});
  T.toggleArenaPatrol(false);
  assert.equal(T.arena.patrolEnabled,true, `${turnCharId}: patrol toggle`);
  T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.clip,'turn', `${turnCharId} right endpoint triggers turn`);
  assert.equal(T.arena.flip,false, `${turnCharId} holds +X facing until turn poses complete`);
  const seenR2L=new Set([T.arena.step]);
  T.arena.keys={KeyD:true}; T.stepAndRenderArena(1000/60); T.arena.keys={};
  assert.equal(T.arena.clip,'turn', `${turnCharId} turn cannot be interrupted mid-spin`);
  seenR2L.add(T.arena.step);
  for(let t=0;t<turnTicks;t++){T.stepAndRenderArena(1000/60);if(T.arena.clip==='turn')seenR2L.add(T.arena.step);}
  assert.equal(seenR2L.size,b.animations.turn.frames.length, `${turnCharId} visits all R->L turn poses`);
  assert.equal(T.arena.flip,true);
  assert.equal(T.arena.clip,'walk', `${turnCharId} resumes walk immediately after R->L turn`);
  Object.assign(T.arena,{x:T.arena.minX+1,patrolDir:-1});
  T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.clip,'turn', `${turnCharId} left endpoint triggers L->R turn`);
  assert.equal(T.arena.flip,true, `${turnCharId} holds -X facing during L->R turn`);
  const seenL2R=new Set([T.arena.step]);
  for(let t=0;t<turnTicks;t++){T.stepAndRenderArena(1000/60);if(T.arena.clip==='turn')seenL2R.add(T.arena.step);}
  assert.equal(seenL2R.size,b.animations.turn.frames.length, `${turnCharId} visits all L->R turn poses`);
  assert.equal(T.arena.flip,false);
  assert.equal(T.arena.clip,'walk');
  // Test run->turn->run endpoint patrol cleanly
  Object.assign(T.arena,{x:T.arena.maxX-1,flip:false,patrolEnabled:false,patrolRun:false,actionClip:null,turnTargetFlip:null});
  T.toggleArenaPatrol(true);
  assert.equal(T.arena.patrolRun,true);
  T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.clip,'turn');
  for(let t=0;t<turnTicks;t++)T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.flip,true);
  assert.equal(T.arena.clip,'run', `${turnCharId} resumes run immediately after endpoint turn`);
  Object.assign(T.arena,{x:560,flip:false,keys:{},hitstop:0,actionClip:null,turnTargetFlip:null,patrolEnabled:false,patrolRun:false});
}

// Verify King Crab horizontal flip rotation WITHOUT a turn clip (left/right movement, patrol endpoints)
const crabChar = apiPayload.roster.characters.find(c => c.character_id === 'tasmanian_king_crab');
if (crabChar) {
  T.selectCharacter('tasmanian_king_crab');
  const cb = T.state.bundlesById[crabChar.modes.combined_1layer.bundle_id];
  assert.equal(T.isSidewaysLocked(cb), false, 'King Crab must NOT be locked to sideways strafe');
  assert.equal(cb.render_contract?.turning?.clip ?? null, null, 'King Crab remains exempt from turn clip');
  assert.equal(cb.animations.turn, undefined, 'King Crab has no turn animation clip');
  assert.equal(T.arena.spawnFacing, 'right', 'King Crab default spawn facing must be right (+X)');
  assert.equal(T.arena.flip, false);
  assert.equal(getEl('arenaSpawnFacingControls').style.display, 'none');
  assert.notEqual(getEl('btnPatrol').style.display, 'none', 'Patrol button must stay visible for unlocked no-turn King Crab');

  // Move left (KeyA): flips left immediately without turn clip and plays walk forward 0..7->0
  const startX = T.arena.x;
  T.arena.keys = { KeyA: true }; T.arena.hitstop = 0; T.arena.actionClip = null;
  const walkStepsSeen = [];
  const totalWalkTicks = cb.animations.walk.frames.reduce((s, f) => s + f.duration_ticks, 0);
  for (let i = 0; i < totalWalkTicks + 6; i++) {
    T.stepAndRenderArena(1000 / 60);
    assert.equal(T.arena.flip, true, 'Moving left rotates King Crab left without needing a turn clip');
    assert.equal(T.arena.clip, 'walk');
    if (walkStepsSeen.at(-1) !== T.arena.step) walkStepsSeen.push(T.arena.step);
  }
  assert.ok(T.arena.x < startX, 'Moving left must decrease X');
  walkStepsSeen.forEach((stepIdx, idx) => assert.equal(stepIdx, idx % cb.animations.walk.frames.length, 'Walk cycle stays forward 0->7->0'));

  // Move right (KeyD): flips back right cleanly
  const leftX = T.arena.x;
  T.arena.keys = { KeyD: true };
  for (let i = 0; i < 6; i++) T.stepAndRenderArena(1000 / 60);
  assert.ok(T.arena.x > leftX, 'Moving right must increase X');
  assert.equal(T.arena.flip, false, 'Moving right rotates King Crab right');
  T.arena.keys = {};

  // Bidirectional flip patrol reverses direction AND facing at bounds without turn clip
  Object.assign(T.arena, { x: T.arena.maxX - 1, patrolEnabled: false, flip: false });
  T.toggleArenaPatrol(false);
  assert.equal(T.arena.patrolEnabled, true);
  assert.equal(T.arena.patrolDir, 1);
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.patrolDir, -1, 'Right bound reverses patrol direction');
  assert.equal(T.arena.flip, true, 'Right bound patrol reversal flips King Crab left');
  assert.equal(T.arena.clip, 'walk');

  Object.assign(T.arena, { x: T.arena.minX + 1 });
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.patrolDir, 1, 'Left bound reverses patrol direction');
  assert.equal(T.arena.flip, false, 'Left bound patrol reversal flips King Crab right');

  T.toggleArenaPatrol(false);
  T.selectCharacter('t_rex');
  assert.equal(getEl('arenaSpawnFacingControls').style.display, 'none');
}

// Summon uses real source crops, shared60Hzcontract and real Rust/WASM flight sampling.
{
  T.selectCharacter('t_rex');
  T.arena.keys={};T.arena.customSpeedPxPerSec=null;
  assert.equal(T.startShenronSummon(),true);
  assert.equal(T.startShenronSummon(),false,'Duplicate trigger must not restart the ritual');
  const config=T.state.api.rituals.shenron_summon;
  const origin=Array.from(T.arena.summon.origin);
  for(let i=0;i<7;i++){
    assert.equal(T.sampleShenronSummon(i*18-1,origin).balls[i].visible,false);
    const launched=T.sampleShenronSummon(i*18,origin).balls[i];
    assert.equal(launched.visible,true);assert.equal(launched.number,i+1);
    assert.deepEqual(Array.from(launched.position),origin);
  }
  const gathered=T.sampleShenronSummon(162,origin);
  for(let i=0;i<7;i++)assert.deepEqual(Array.from(gathered.balls[i].position),config.items[i].formation_offset_px.map((v,k)=>v+config.layout.map_center_px[k]));
  assert.equal(T.sampleShenronSummon(227,origin).groundAlpha,0);
  assert.equal(T.sampleShenronSummon(246,origin).groundAlpha,0);
  assert.equal(T.sampleShenronSummon(246,origin).dragonAlpha,0);
  assert.equal(T.sampleShenronSummon(230,origin).flashAlpha,1);
  assert.equal(T.sampleShenronSummon(230,origin).groundAlpha,0);
  assert.equal(T.sampleShenronSummon(240,origin).flashAlpha,0);
  assert.equal(T.sampleShenronSummon(240,origin).groundAlpha,0);
  assert.equal(T.sampleShenronSummon(250,origin).flashAlpha,1);
  assert.equal(T.sampleShenronSummon(250,origin).groundAlpha,1);
  assert.ok(T.sampleShenronSummon(250,origin).dragonAlpha>0.5);
  assert.equal(T.sampleShenronSummon(254,origin).flashAlpha,0.5);
  assert.equal(T.sampleShenronSummon(254,origin).groundAlpha,1);
  assert.ok(T.sampleShenronSummon(254,origin).dragonAlpha>0.85);
  assert.equal(T.sampleShenronSummon(256,origin).flashAlpha,0);
  assert.equal(T.sampleShenronSummon(256,origin).groundAlpha,1);
  assert.ok(T.sampleShenronSummon(256,origin).dragonAlpha>=0.97);
  assert.ok(Math.abs(T.sampleShenronSummon(252,origin).dragonAlpha-0.75)<1e-9);
  for(let tick=250;tick<600;tick++)assert.ok(T.sampleShenronSummon(tick,origin).glowAlpha>=0.78);
  const ready=T.sampleShenronSummon(258,origin);
  assert.equal(ready.groundRect[2],144);assert.ok(Math.abs(ready.groundRect[1]+ready.groundRect[3]-840)<1e-8);
  assert.equal(ready.dragonPosition[0],960);assert.equal(ready.dragonAlpha,1);
  assert.equal(config.reveal.method,'pixel_dissolve');
  const maskKey='/'+config.reveal.mask;
  const origMask=T.state.images[maskKey];
  assert.ok(origMask,'Threshold mask must be preloaded by initApp()');
  {
    const mw=config.reveal.mask_size_px[0],mh=config.reveal.mask_size_px[1];
    const maskRgba=new Uint8ClampedArray(mw*mh*4);
    maskRgba[0]=250;maskRgba[3]=255;
    maskRgba[4]=0;maskRgba[7]=255;
    maskRgba[8]=50;maskRgba[11]=255;
    T.state.images[maskKey]={_mockRgba:maskRgba};
    const w=12,h=4;
    const mkBuf=()=>{const b=new Uint8ClampedArray(w*h*4);for(let x=0;x<w;x++){const k=x*4;b[k]=40;b[k+1]=120;b[k+2]=60;b[k+3]=255;}return b;};
    let putCount=0,activeBuf=mkBuf();
    const dissolveCtx={getImageData:()=>({data:activeBuf}),putImageData:(img)=>{putCount++;activeBuf=img.data;}};
    T.applyShenronPixelDissolve(dissolveCtx,w,h,0.25);
    assert.equal(putCount,1);
    assert.equal(activeBuf[3],0,'Cell 0 (threshold 250) must be hidden at progress=0.25');
    assert.equal(activeBuf[4*4+3],255,'Cell 1 (threshold 0) must be revealed at progress=0.25');
    assert.equal(activeBuf[4*4],40,'Cell 1 outside edge band keeps source R');
    assert.equal(activeBuf[8*4+3],255,'Cell 2 (threshold 50) must be revealed at progress=0.25');
    assert.ok(activeBuf[8*4]>40&&activeBuf[8*4+1]>120&&activeBuf[8*4+2]>60,'Cell 2 inside edge band tints toward edge_color_rgb');
    const fullBuf=mkBuf();
    const beforeFull=Array.from(fullBuf);
    activeBuf=fullBuf;
    T.applyShenronPixelDissolve(dissolveCtx,w,h,1.0);
    assert.equal(putCount,1,'progress>=1 must short-circuit without putImageData');
    assert.deepEqual(Array.from(fullBuf),beforeFull,'progress>=1 preserves pixels untouched');
    T.state.images[maskKey]=origMask;
  }
  T.arena.summon.tick=0;T.stepAndRenderArena(16,100);assert.ok(Math.abs(T.arena.summon.tick-6)<1e-9,'Ritual uses uncapped wall time under slow rendering');
  const casterX=T.arena.x,casterY=T.arena.y;T.arena.keys={KeyD:true,KeyW:true};
  T.stepAndRenderArena(1000/60);assert.equal(T.arena.x,casterX);assert.equal(T.arena.y,casterY);
  T.arena.summon.tick=10000;T.arena.keys={};T.stepAndRenderArena(1000/60);
  assert.ok(T.arena.summon,'Persist until wish or explicit dismiss');
  assert.equal(getEl('shenronWishOverlay').style.display,'block','Wish overlay opens once ready_tick is reached');
  assert.equal(getEl('shenronWishButtons').children.length,3,'Three sample wishes loaded from sequence.json');
  const hpBeforeWish=T.arena.dummyHp;
  getEl('shenronWishButtons').children[0].click();
  assert.equal(T.arena.dummyHp,hpBeforeWish,'Wish selection notice-only must not modify combat stats');
  assert.equal(getEl('shenronWishOverlay').style.display,'none','Wish overlay closes immediately after selecting a wish');
  assert.ok(T.arena.summon?.dismissing,'Selecting wish auto-starts 2-flash dismiss');
  assert.ok(T.arena.wishNotice&&T.arena.wishNotice.lifeMs>0,'Wish notice banner displays confirmation');
  assert.equal(T.sampleShenronDismiss(2,origin,258).flashAlpha,1);
  assert.equal(T.sampleShenronDismiss(14,origin,258).elementsVisible,true);
  assert.equal(T.sampleShenronDismiss(20,origin,258).flashAlpha,1);
  assert.equal(T.sampleShenronDismiss(20,origin,258).elementsVisible,false);
  assert.equal(T.sampleShenronDismiss(28,origin,258).flashAlpha,0);
  assert.equal(T.sampleShenronDismiss(28,origin,258).finished,true);
  for(let s=0;s<30&&T.arena.summon;s++)T.stepAndRenderArena(1000/60);
  assert.equal(T.arena.summon,null,'2-flash dismiss clears summon cleanly after tick 28');
  assert.equal(T.startShenronSummon(),true,'Auto-dismiss permits clean replay');
  T.arena.summon.tick=258;
  assert.equal(T.startShenronDismiss(),true,'Manual Thu hoi button also triggers 2-flash dismiss');
  assert.ok(T.arena.summon.dismissing);
  T.dismissShenronSummon();assert.equal(T.arena.summon,null);
  const dismissTicks=[0,2,6,10,14,18,19,20,22,24,26,28];
  const dismissTrace=dismissTicks.map(t=>{const d=T.sampleShenronDismiss(t,[560,650],258);return {tick:t,flash_alpha:d.flashAlpha,phase:d.phase,ground_alpha:d.groundAlpha,glow_alpha:d.glowAlpha,dragon_position:Array.from(d.dragonPosition),dragon_alpha:d.dragonAlpha,dragon_frame:d.dragonFrame,elements_visible:d.elementsVisible,finished:d.finished};});
  const ticks=[0,18,27,54,108,162,210,219,228,230,240,246,247,248,250,252,254,256,257,258,266,284,330,10000];
  const trace=ticks.map(tick=>{const s=T.sampleShenronSummon(tick,[560,650]);return {reveal_top:s.revealTop,flash_alpha:s.flashAlpha,tick,phase:s.phase,balls:s.balls.map(b=>({number:b.number,visible:b.visible,alpha:b.alpha,position:Array.from(b.position)})),ground_rect:Array.from(s.groundRect),ground_alpha:s.groundAlpha,glow_alpha:s.glowAlpha,dragon_position:Array.from(s.dragonPosition),dragon_alpha:s.dragonAlpha,dragon_frame:s.dragonFrame};});
  console.log('SHENRON_SUMMON_TRACE='+JSON.stringify(trace));
  console.log('SHENRON_DISMISS_TRACE='+JSON.stringify(dismissTrace));
}

// Phase B: Inject synthetic 1-Layer Combined characters to verify dynamic multi-character pipeline
const makeMockBundle = (id, cw, ch) => {
  const mkFrames = (n, dur = 60.0) => Array.from({ length: n }, (_, idx) => ({
    sub_id: `${id}_f${idx}`,
    duration_ticks: 4,
    duration_ms: dur,
    atlas_file: `${id}-atlas-00.png`,
    atlas_url: `/assets/${id}/godot_bundle/godot/${id}-atlas-00.png`,
    x: idx * cw,
    y: 0,
    w: cw,
    h: ch,
  }));
  return {
    id,
    name: id,
    frame_size: [cw, ch],
    anchor_px: [96, 220],
    sha256_tres: '0'.repeat(64),
    sha256_atlases: { [`${id}-atlas-00.png`]: 'a'.repeat(64) },
    animations: {
      idle: { name: 'idle', loop: true, speed_hz: 60.0, frames: mkFrames(1, 500.0) },
      aura_loop: { name: 'aura_loop', loop: true, speed_hz: 60.0, frames: mkFrames(4, 83.33) },
      power_up: { name: 'power_up', loop: false, speed_hz: 60.0, frames: mkFrames(4, 60.0) },
      attack_light: { name: 'attack_light', loop: false, speed_hz: 60.0, frames: mkFrames(4, 60.0) },
      hit: { name: 'hit', loop: false, speed_hz: 60.0, frames: mkFrames(2, 83.33) },
    },
  };
};

const makeMockChar = (id, name, cw, ch) => ({
  character_id: id,
  display_name: name,
  faction: 'z_fighters',
  role_label: 'Synthetic 1-Layer Test Fighter',
  tags: ['test'],
  status: 'finalized_ready_for_human_test',
  map_sync_metrics: {
    canvas_size_px: [cw, ch],
    foot_anchor_px: [96, 220],
    body_only_bbox_px: { x: 80, y: 160, w: 32, h: 60 },
    full_fx_bbox_px: { x: 20, y: 50, w: 240, h: 180 },
    world_size_at_64ppu_m: { body_w_m: 0.5, body_h_m: 0.94, aura_w_m: 3.75, aura_h_m: 2.81 },
    tile_32px_span: { body_tiles_w: 1.0, body_tiles_h: 1.88, full_fx_tiles_w: 7.5, full_fx_tiles_h: 5.63 },
  },
  pixel_sharpness_metrics: {
    texel_scale_ratio: '1:1 Nearest',
    edge_acutance_sobel: 380.0,
    alpha_hardness_pct: 100.0,
    opaque_key_px: 0,
    enclosed_key_pockets: 0,
    outer_ring_spill_fraction: 0.0,
  },
  present_clips: ['idle', 'aura_loop', 'power_up', 'attack_light', 'hit'],
  missing_provisional_clips: [],
  modes: {
    combined_1layer: {
      label: 'Combined 1-Layer',
      godot_prefab: `res://scenes/${id}.tscn`,
      bundle_id: id,
    },
  },
});

const b1 = makeMockBundle('hero_alpha_test', 288, 256);
const b2 = makeMockBundle('hero_beta_test', 320, 256);
T.state.bundlesById[b1.id] = b1;
T.state.bundlesById[b2.id] = b2;
T.state.images[`/assets/${b1.id}/godot_bundle/godot/${b1.id}-atlas-00.png`] = new sandbox.Image();
T.state.images[`/assets/${b2.id}/godot_bundle/godot/${b2.id}-atlas-00.png`] = new sandbox.Image();
const expectedRosterCount = T.state.api.roster.characters.length + 2;
T.state.api.roster.characters.push(
  makeMockChar('hero_alpha_test', 'Hero Alpha (Test)', 288, 256),
  makeMockChar('hero_beta_test', 'Hero Beta (Test)', 320, 256),
);

T.selectCharacter('hero_alpha_test');
T.renderInspector();
assert.equal(T.state.activeChar.character_id, 'hero_alpha_test');
assert.equal(T.state.archMode, 'combined_1layer');
assert.deepEqual(Array.from(T.getCanvasSize()), [288, 256], 'Inspector must dynamically adopt 288x256 canvas from roster.json');
assert.equal(getEl('inspectorCanvas').width, 288 * 2 + 28, 'Inspector canvas at 2x zoom must be 604px wide');
assert.equal(getEl('inspectorCanvas').height, 256 * 2 + 28, 'Inspector canvas at 2x zoom must be 540px high');

// Test 1: Play a oneshot clip ('power_up', 4 frames) with autoReplayOneshot = false until it stops, then click Play!
T.state.activeClipName = 'power_up';
T.state.autoReplayOneshot = false;
T.state.stepIdx = 0;
T.state.stepElapsedMs = 0;
T.state.playing = true;

for (let i = 0; i < 20; i++) {
  T.stepInspectorAnimation(60.0);
}
assert.equal(T.state.playing, false, 'Oneshot clip with autoReplay=false must pause cleanly at final frame');
assert.equal(getEl('btnPlayPause').textContent, '▶ Phát lại từ đầu');

getEl('btnPlayPause').click();
assert.equal(T.state.playing, true, 'Clicking Play after oneshot ends MUST resume playing');
assert.equal(T.state.stepIdx, 0, 'Clicking Play after oneshot ends MUST rewind stepIdx to 0');
T.stepInspectorAnimation(120.0);
assert.ok(T.state.stepIdx >= 1, 'Animation must advance past frame 0 after clicking Play');

// Test 2: Switch to Tab 2 (Landscape 16:9 1920x1080 Mobile Arena) & verify bezel/map/scale parity!
tabArenaBtn.click();
assert.equal(T.state.activeTab, 'tab-arena');
assert.equal(getEl('arenaCanvas').width, 1920, 'Arena canvas must be 1920px wide (16:9 Landscape)');
assert.equal(getEl('arenaCanvas').height, 1080, 'Arena canvas must be 1080px tall (16:9 Landscape)');
assert.equal(T.arena.groundY, 840);
assert.equal(T.arena.charScale, 2, 'Arena default character scale must be 2x Nearest');
getEl('btnScale3').click();
assert.equal(T.arena.charScale, 3);
getEl('btnScale1').click();
assert.equal(T.arena.charScale, 1);
T.setArenaCharacterScale(1.5);
assert.equal(T.arena.charScale, 1.5, 'Arena must support fractional character scale (1.5x)');
assert.ok(getEl('arenaStageBadge').textContent.includes('1.5× Nearest'), 'Stage badge must show fractional scale readout');
getEl('btnScale2').click();
assert.equal(T.arena.charScale, 2);
getEl('chkPhoneBezel').onchange({ target: { checked: false } });
assert.equal(getEl('arenaPhoneBezelImg').style.display, 'none');
getEl('chkNative1to1').onchange({ target: { checked: true } });
assert.equal(getEl('arenaPhoneFrame').style.width, '1920px', 'Native 1:1 toggle must render exact 1920px CSS width');
getEl('chkNative1to1').onchange({ target: { checked: false } });
getEl('chkPhoneBezel').onchange({ target: { checked: true } });
assert.equal(getEl('arenaPhoneBezelImg').style.display, 'block');
assert.equal(T.arena.burrowDustScale, 2.65, 'Burrow dust FX runtime scale must default to 2.65x');

T.arena.x = 560; T.arena.dummyX = 1360;
const hpBefore = T.arena.dummyHp;
const burstBtn = getEl('arenaSkillButtons').children.find(b => b.dataset.clip === 'power_up');
assert.ok(burstBtn, 'Tab 3 must dynamically render power_up skill button');
burstBtn.click();
assert.equal(T.arena.shake, 0, 'Screen shake must be completely disabled on attack');
for (let i = 0; i < 6; i++) {
  T.stepAndRenderArena(20.0);
}
assert.equal(T.arena.dummyHp, hpBefore - 250, 'power_up in Tab 3 must deal 250 DMG to dummy');

T.arena.x = 1220;
const atkBtn = getEl('arenaSkillButtons').children.find(b => b.dataset.clip === 'attack_light');
assert.ok(atkBtn, 'Tab 3 must dynamically render attack_light skill button');
atkBtn.click();
assert.equal(T.arena.shake, 0, 'Screen shake must stay 0 on melee attack');
for (let i = 0; i < 6; i++) {
  T.stepAndRenderArena(20.0);
}
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 3 Gameplay Arena must run with ZERO runtime errors');
assert.equal(T.arena.dummyHp, hpBefore - 250 - 120, 'attack_light at melee range in Tab 3 must deal 120 DMG to dummy');
assert.ok(getEl('arenaCanvas')._ctx2d._drawCalls > 10, 'Tab 3 Arena Canvas must actively draw stage, dummy, and player');
assert.equal(getEl('arenaCanvas')._ctx2d._ellipseCalls, 0, 'Tab 3 Arena must NOT draw circular ground shadows');
assert.equal(getEl('inspectorCanvas')._ctx2d._ellipseCalls, 0, 'Tab 1 Inspector must NOT draw circular ground shadows');

// Test 4: Switch to 2nd character & verify dynamic canvas resize + roster list count
T.selectCharacter('hero_beta_test');
assert.equal(T.state.activeChar.character_id, 'hero_beta_test');
assert.deepEqual(Array.from(T.getCanvasSize()), [320, 256]);
assert.equal(getEl('rosterList').children.length, expectedRosterCount, 'Roster list must render all N finalized characters');

// An independent aura does not require a projectile ability.
b1.animations.walk={name:'walk',loop:true,speed_hz:60,frames:b1.animations.attack_light.frames.slice(0,2)};
b1.render_contract = {
  body_clips: ['idle','walk','attack_light','power_up','hit'],
  effect_clips: ['aura_loop'],
  locomotion: {clip:'walk'},
  aura: {loop_clip:'aura_loop',charge_clip:null,independent_clock:true},
};
T.selectCharacter('hero_alpha_test');
const auraOnly=T.getLayerFramesForStep('walk',0,{auraEnabled:true,fxTicks:4});
assert.deepEqual(Array.from(auraOnly,x=>x.layer),['Aura','Body']);
assert.equal(auraOnly[0].frame,b1.animations.aura_loop.frames[1]);
assert.equal(auraOnly[1].frame,b1.animations.walk.frames[0]);
assert.equal(T.getLayerFramesForStep('walk',0,{auraEnabled:false}).length,1);
T.state.activeClipName='walk';
T.state.auraEnabled=true;
T.renderInspector();
assert.equal(getEl('runtimeErrorBanner').textContent,'');

// Freehand selection: exercise real pointer handlers with CSS-scaled canvas,
// concave mask, exact exported runs, and pixels excluded from RGB statistics.
const inspector = getEl('inspectorCanvas');
inspector.getBoundingClientRect = () => ({left:17,top:23,width:inspector.width/2,height:inspector.height/2});
const emitPointer = (type,x,y) => {
  const ev = {type, pointerId:1, button:0, preventDefault() {},
    clientX:17+(28+x*T.state.zoom)/2, clientY:23+(28+y*T.state.zoom)/2};
  for (const fn of inspector._listeners[type] || []) fn(ev);
};
const oldRead = T.offCtx.getImageData;
T.offCtx.getImageData = (x,y,w,h) => {
  const data = new Uint8ClampedArray(w*h*4);
  for (let row=0;row<h;row++) for (let col=0;col<w;col++) {
    const excluded = x+col>=14 && y+row>=14;
    data.set(excluded ? [250,0,0,255] : [20,40,60,255], (row*w+col)*4);
  }
  return {data};
};
getEl('selSelectionMode').onchange({target:{value:'lasso'}});
T.state.playing=true;
emitPointer('pointerdown',10,10);
for (const [x,y] of [[20,10],[20,14],[14,14],[14,20]]) emitPointer('pointermove',x,y);
emitPointer('pointerup',10,20); // final point must be included even without move
assert.equal(T.state.playing,false,'Selection freezes the displayed pose');
const runs=Array.from(T.selectionPixelRuns(T.state.selectedRect,T.state.selectedPolygon),r=>Array.from(r));
assert.equal(runs.reduce((n,r)=>n+r[2],0),64,'Concave lasso excludes the 6x6 notch');
assert.equal(runs.some(([y,x,len])=>y>=14 && x+len>14),false);
let text=getEl('txtAgentSpec').value;
assert.match(text,/Canvas Lasso/);
assert.match(text,/64\/64 pixel có hình, RGB trung bình=\[20, 40, 60\]/);
const copiedRuns=JSON.parse(text.match(/PixelRuns Canvas \[y,x,length\] \(mặt nạ chính xác\): (.*)/)[1]);
assert.deepEqual(copiedRuns,runs,'Copy must preserve the exact mask used by statistics');
T.renderInspector(); // closed freehand overlay must render without canvas errors
getEl('btnAddPin').click();
assert.equal(T.state.pinnedSpecs.at(-1),text,'Pins preserve the freehand mask');
getEl('selSelectionMode').onchange({target:{value:'rect'}});
emitPointer('pointerdown',20,20); emitPointer('pointerup',10,10);
assert.equal(T.state.selectedPolygon,null);
assert.deepEqual(JSON.parse(JSON.stringify(T.state.selectedRect)),{x:10,y:10,w:11,h:11});
assert.match(getEl('txtAgentSpec').value,/Canvas Rect\(10, 10, 11, 11\)/);
assert.match(getEl('txtAgentSpec').value,/121\/121 pixel có hình/);
getEl('btnClearRect').click();
assert.equal(T.state.selectedRect,null);
getEl('selSelectionMode').onchange({target:{value:'lasso'}});
emitPointer('pointerdown',10,10); emitPointer('pointerup',10,10);
assert.equal(T.state.selectedRect,null,'Degenerate lasso must clear instead of selecting bbox');
emitPointer('pointerdown',10,10); emitPointer('pointermove',20,20); emitPointer('pointercancel',20,20);
assert.equal(T.state.selectedRect,null,'Cancelled touch gestures clear their unfinished selection');
T.offCtx.getImageData=oldRead;

// Review links select an actual character/clip/frame and pause without advancing it.
const reviewCharacter=apiPayload.roster.characters.find(ch =>
  T.state.bundlesById[ch.modes.combined_1layer.bundle_id]?.animations.walk);
if (reviewCharacter) {
  sandbox.URLSearchParams=URLSearchParams;
  sandbox.location={search:`?character=${encodeURIComponent(reviewCharacter.character_id)}&clip=walk&frame=0&paused=1`};
  await T.initApp();
  assert.equal(T.state.activeChar.character_id,reviewCharacter.character_id);
  assert.equal(T.state.activeClipName,'walk');
  assert.equal(T.state.stepIdx,0);
  assert.equal(T.state.playing,false);
  sandbox.location.search=`?character=${encodeURIComponent(reviewCharacter.character_id)}&clip=walk&frame=999&paused=1`;
  await T.initApp();
  const animation=T.state.bundlesById[reviewCharacter.modes.combined_1layer.bundle_id].animations.walk;
  assert.equal(T.state.stepIdx,animation.frames.length-1,'Review frame must clamp to the selected animation');
  assert.equal(getEl('runtimeErrorBanner').textContent,'');
}

// Stationary AI must idle even outside the patrol zone and retain its facing.
{
  const ai = {};
  const decision = T.evaluateUtilityAI(ai, { is_stationary: true, facing_left: true, target_x: 9000 });
  assert.equal(decision.intent, 'idle');
  assert.equal(decision.move_dir, 0);
  assert.equal(decision.attack_clip, '');
  assert.equal(decision.desired_face_left, true);
}

// Phase G: Shared 1:1 Utility AI Verification (Mirror of Godot UtilityAIController.gd + ArenaSandbox.gd)
if (apiPayload.roster.characters.length > 0) {
  tabArenaBtn.click();
  assert.equal(T.arena.utilityAiCfg.close_edge_px, 50);
  assert.equal(T.arena.utilityAiCfg.mid_max_edge_px, 200);
  assert.equal(T.arena.utilityAiCfg.heavy_max_edge_px, 200);
  assert.equal(T.arena.utilityAiCfg.attack_cooldown_s, 1.0);
  assert.equal(T.arena.utilityAiCfg.light_hits_before_heavy, 2);
  assert.equal(T.arena.utilityAiCfg.zone_width_max_px, 500);

  const rA = T.computeBodyRect(1000, 840, 100, 100, 1);
  const rB = T.computeBodyRect(1140, 840, 100, 100, 1);
  assert.ok(Math.abs(T.computeEdgeDistance(rA, rB) - 40) < 0.01, 'Body edge distance must subtract body half-widths');

  // T-Rex: Patrol outside zone -> Chase [50,200) -> Light1 -> Cooldown -> Light2 -> Heavy (<200px) -> Far PowerUp reset
  T.selectCharacter('t_rex');
  T.setArenaCharacterScale(1.0);
  T.setUtilityAiEnabled(true);
  assert.ok(T.arena.enemyAi.zoneMaxX - T.arena.enemyAi.zoneMinX <= 500, 'Zone width must stay <=500px');
  T.arena.x = 560; T.arena.y = 840;
  let stepRes = T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastIntent, 'patrol');

  T.arena.enemyAi.x = 1500;
  T.arena.x = 1200; // edge gap = 300 - 186 = 114px in [50, 200)
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastIntent, 'chase');

  T.arena.x = 1285; // edge gap = 215 - 186 = 29px < 50px
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light');
  assert.equal(T.arena.enemyAi.lightChainCount, 1);

  T.stepEnemyAiFrame(16.67); // busy while executing Light 1
  assert.equal(T.arena.enemyAi.lastIntent, 'busy');

  T.arena.enemyAi.actionClip = null;
  T.arena.enemyAi.cooldownRemaining = 0;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light');
  assert.equal(T.arena.enemyAi.lightChainCount, 2);

  T.arena.enemyAi.actionClip = null;
  T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.x = 1210; // still in [1120,1600], edge gap = 104px < 200px -> Heavy follow-up!
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_heavy');
  assert.equal(T.arena.enemyAi.lightChainCount, 0);

  // Run out to >=200px after 2 lights -> PowerUp + Reset Chain
  T.setUtilityAiEnabled(true);
  T.arena.enemyAi.x = 1550;
  T.arena.x = 1335;
  T.stepEnemyAiFrame(16.67);
  T.arena.enemyAi.actionClip = null; T.arena.enemyAi.cooldownRemaining = 0;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lightChainCount, 2);
  T.arena.enemyAi.actionClip = null; T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.x = 1140; // edge gap >= 200px within zone [1120, 1600]
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'power_up');
  assert.equal(T.arena.enemyAi.lightChainCount, 0);

  // Dilophosaurus (no heavy) stays on attack_light after 2 lights
  T.selectCharacter('dilophosaurus');
  T.setArenaCharacterScale(1.0);
  T.setUtilityAiEnabled(true);
  T.arena.enemyAi.x = 1500;
  T.arena.x = 1330;
  T.arena.enemyAi.lightChainCount = 2;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light');

  // Flying mob (bat_chiroptera): hover y=250, no chase >=50px -> power_up, close <50px -> attack_light
  T.selectCharacter('bat_chiroptera');
  assert.ok(Math.abs(T.arena.charScale - 1.1) < 1e-4);
  T.setArenaCharacterScale(1.0);
  T.setUtilityAiEnabled(true);
  assert.equal(T.arena.enemyAi.y, 250);
  T.arena.x = 1160; T.arena.y = 840;
  const fStartX = T.arena.enemyAi.x;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'power_up');
  assert.equal(T.arena.enemyAi.x, fStartX);
  T.arena.enemyAi.actionClip = null; T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.x = 1340; T.arena.y = 250;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light');

  // Verify calibrated default scales + pteranodon/crab instant flip burst + smooth bat walk->turn->walk
  const expectedScales = {
    chilopoda: 1.35, bat_chiroptera: 1.1, spinosaurus: 2.0, t_rex: 1.75,
    pteranodon: 1.5, tasmanian_king_crab: 1.25, sarcosuchus: 2.0, dilophosaurus: 1.75,
  };
  for (const [cid, scl] of Object.entries(expectedScales)) {
    T.selectCharacter(cid);
    assert.ok(Math.abs(T.arena.charScale - scl) < 1e-4, `${cid} default charScale ${T.arena.charScale} != ${scl}`);
  }
  T.selectCharacter('pteranodon');
  T.arena.flip = false; T.arena.keys = { KeyA: true }; T.arena.hitstop = 0;
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.flip, true);
  assert.ok(T.arena.turnBoostMs > 200, 'Pteranodon turnaround speed burst activated');
  T.selectCharacter('tasmanian_king_crab');
  T.arena.flip = false; T.arena.keys = { KeyA: true }; T.arena.hitstop = 0;
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.flip, true);
  assert.ok(T.arena.turnBoostMs > 200, 'King Crab turnaround speed burst activated');
  T.selectCharacter('bat_chiroptera');
  T.arena.flip = false; T.arena.clip = 'walk'; T.arena.keys = { KeyA: true };
  T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.clip, 'turn');
  for (let i = 0; i < 16; i++) T.stepAndRenderArena(1000 / 60);
  assert.equal(T.arena.flip, true);
  assert.equal(T.arena.clip, 'walk', 'Bat resumes walk immediately after turn without idle flash');
  T.arena.keys = {};

  // Chilopoda: <50px laser power_up, >=50px burrow attack_light targeting player X
  T.selectCharacter('chilopoda');
  T.setArenaCharacterScale(1.0);
  T.setUtilityAiEnabled(true);
  T.arena.enemyAi.x = 1500; T.arena.y = 840;
  T.arena.x = 1330;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'power_up');
  T.arena.enemyAi.actionClip = null; T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.x = 1200;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.lastAttackClip, 'attack_light');
  assert.ok(T.arena.enemyAi.chiloAction && Array.isArray(T.arena.enemyAi.chiloAction.target));

  // Tasmanian King Crab: spawns facing left (-X), rotates toward player behind its back (+X or -X) before firing power_up
  T.selectCharacter('tasmanian_king_crab');
  T.setArenaCharacterScale(2.0);
  T.setUtilityAiEnabled(true);
  assert.equal(T.arena.enemyAi.flip, true, 'Unlocked King Crab AI enemy spawns facing left (-X) toward player');
  // Player stands behind Crab inside zone [1120..1600] on +X side (edge gap 204px >=200) -> Crab flips right (flip=false) before firing power_up
  T.arena.enemyAi.x = 1125;
  T.arena.x = 1595;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.flip, false, 'Crab AI must rotate right toward player behind its back');
  assert.equal(T.arena.enemyAi.lastAttackClip, 'power_up');
  assert.equal(T.arena.enemyAi.actionClip, 'power_up');
  // Reset AI action & cooldown, move Player behind Crab again inside zone on -X side (edge gap 202px >=200) -> Crab flips left (flip=true)
  T.arena.enemyAi.actionClip = null;
  T.arena.enemyAi.cooldownRemaining = 0;
  T.arena.enemyAi.x = 1590;
  T.arena.x = 1122;
  T.stepEnemyAiFrame(16.67);
  assert.equal(T.arena.enemyAi.flip, true, 'Crab AI must rotate left toward player behind its back');
  assert.equal(T.arena.enemyAi.lastAttackClip, 'power_up');
  assert.equal(T.arena.enemyAi.actionClip, 'power_up');
  T.stepAndRenderArena(16.67);
  assert.match(getEl('arenaAiStatus').textContent, /AI\[tasmanian_king_crab\]/);
  T.setUtilityAiEnabled(false);
  tabHumanBtn.click();
}

// Verify Dragon Ball 1x (32x32) item pack + diagonal sheen + hide toggle + 10px monster drop/roll + shrink pickup
{
  const dbItem = T.state.itemsById?.dragon_balls;
  assert.ok(dbItem, 'apiPayload.items.by_id.dragon_balls must be loaded');
  assert.deepEqual(dbItem.frame_size, [32, 32]);
  assert.equal(dbItem.animations.sparkle_fx.frames.length, 8);
  assert.equal(dbItem.sparkle_fx.style, 'diagonal_body_sheen');
  assert.equal(dbItem.sparkle_fx.show_in_bag, false);
  assert.equal(T.arena.itemDrop.enabled, true);
  assert.equal(T.arena.itemDrop.scale, 1.0);

  // Toggle hide/show button on arena toolbar
  getEl('btnToggleArenaItems').click();
  assert.equal(T.arena.itemDrop.enabled, false);
  getEl('btnToggleArenaItems').click();
  assert.equal(T.arena.itemDrop.enabled, true);

  // Monster death drop: jumps 10px, falls to groundY, rolls ~10px, then transitions to resting sheen
  T.arena.itemDrop.drops = [];
  T.arena.itemDrop.collectedBalls = [];
  const dObj = T.triggerArenaMonsterDrop(3);
  let minY = dObj.y;
  let landX = dObj.x;
  let sawFall = false, sawRoll = false;
  for (let tick = 0; tick < 55; tick++) {
    T.stepArenaItemDrops(1000 / 60);
    minY = Math.min(minY, dObj.y);
    if (dObj.phase === 'dropping' && dObj.subphase === 'fall') {
      sawFall = true;
      landX = dObj.x;
    } else if (dObj.phase === 'dropping' && dObj.subphase === 'roll') {
      sawRoll = true;
    } else if (dObj.phase === 'resting') {
      break;
    }
  }
  assert.ok(Math.abs((T.arena.groundY - minY) - 10.0) < 0.4, `Expected 10px jump, got ${T.arena.groundY - minY}`);
  assert.ok(sawFall && sawRoll, 'Drop must pass fall and roll subphases');
  assert.equal(dObj.phase, 'resting');
  assert.ok(Math.abs(dObj.x - landX) >= 8.0 && Math.abs(dObj.x - landX) <= 13.5, 'Roll must move ~10px');

  // Pickup shrinks monotonically (20% slower = 30 ticks @ 60Hz) until reaching player and recording in bag
  const started = T.pickupArenaItems(0);
  assert.equal(started, 1);
  let prevScale = dObj.scale;
  let stillCollectingAt24 = false;
  for (let tick = 0; tick < 36; tick++) {
    T.stepArenaItemDrops(1000 / 60);
    if (tick === 23 && dObj.phase === 'collecting') stillCollectingAt24 = true;
    if (dObj.phase === 'collecting') {
      assert.ok(dObj.scale <= prevScale + 1e-6);
      prevScale = dObj.scale;
    }
  }
  assert.ok(stillCollectingAt24, '20% slower pickup (30 ticks) must still be collecting at tick 24');
  assert.equal(dObj.phase, 'collected');
  assert.ok(T.arena.itemDrop.collectedBalls.includes(3));

  T.renderDragonBallItemInspector();
  tabArenaBtn.click();
  T.stepAndRenderArena(16.67);
  tabHumanBtn.click();
}

// Verify D1/D2/D4 mobile expand profiles, <1080p Fractional guard, and Godot Web toggle
{
  tabArenaBtn.click();
  assert.ok(Array.isArray(T.arena.deviceProfiles) && T.arena.deviceProfiles.length >= 4, 'Device profiles must load in preview');

  getEl('selDeviceProfile').onchange({ target: { value: 'redmi_k70e' } });
  T.stepAndRenderArena(16.67);
  assert.equal(getEl('arenaCanvas').width, 2401, 'Redmi K70E (2712x1220) fractional expand must expand width to 2401px');
  assert.equal(getEl('arenaCanvas').height, 1080);
  assert.equal(getEl('arenaPhoneFrame').style.aspectRatio, '2712 / 1220');
  assert.equal(T.arena.showGridOverlay, false, 'Boundary/grid overlay must default off');
  assert.ok(T.arena.minX < 0 && T.arena.maxX > 1920, `K70E walkable bounds must expand across visible width: [${T.arena.minX}, ${T.arena.maxX}]`);

  getEl('chkPixelPerfect').onchange({ target: { checked: true } });
  const k70eInt = T.computeDeviceLayoutMetrics(T.getSelectedDeviceProfile(), true);
  assert.equal(k70eInt.integerApplied, true, 'Pixel Perfect integer must activate on 1220p (>=1080)');
  assert.equal(getEl('arenaCanvas').width, 2712);

  getEl('selDeviceProfile').onchange({ target: { value: 'ipad_10th' } });
  const ipadFrac = T.computeDeviceLayoutMetrics(T.getSelectedDeviceProfile(), false);
  assert.equal(ipadFrac.visW, 1920);
  assert.equal(ipadFrac.visH, 1334);
  const ipadInt = T.computeDeviceLayoutMetrics(T.getSelectedDeviceProfile(), true);
  assert.equal(ipadInt.integerApplied, true);
  assert.equal(ipadInt.visW, 2360);
  assert.equal(ipadInt.visH, 1640);

  getEl('selDeviceProfile').onchange({ target: { value: 'android_720p_20_9' } });
  const p720 = T.computeDeviceLayoutMetrics(T.getSelectedDeviceProfile(), true);
  assert.equal(p720.below1080p, true);
  assert.equal(p720.integerApplied, false, '<1080p device must lock Fractional to avoid Godot integer upscale clipping');
  assert.equal(getEl('arenaCanvas').width, 2400);
  assert.ok(getEl('arenaStageBadge').textContent.includes('Fractional'), '720p badge must show Fractional guard');

  // Toggle real Godot Web runtime iframe when build/web/index.html exists
  if (apiPayload.godot_web_ready) {
    getEl('chkGodotWebRuntime').onchange({ target: { checked: true } });
    assert.equal(getEl('godotWebFrame').style.display, 'block');
    assert.ok(getEl('godotWebFrame').src.endsWith('/godot-web/index.html'));
    getEl('chkGodotWebRuntime').onchange({ target: { checked: false } });
    assert.equal(getEl('godotWebFrame').style.display, 'none');
  }

  // Verify pinned-top arena stage & unpin toggle
  assert.equal(T.arena.pinArenaStage, true, 'Arena stage must pin at top by default');
  assert.ok(html.indexOf('id="arenaPinnedStage"') < html.indexOf('id="arenaSettingsCard"'), 'Pinned arena stage must appear above settings panels');
  getEl('chkPinArenaStage').onchange({ target: { checked: false } });
  assert.equal(T.arena.pinArenaStage, false);
  assert.equal(getEl('arenaPinnedStage').classList._set.has('unpinned'), true);
  getEl('chkPinArenaStage').onchange({ target: { checked: true } });
  assert.equal(T.arena.pinArenaStage, true);
  assert.equal(getEl('arenaPinnedStage').classList._set.has('unpinned'), false);

  // Verify Rocky Plateau Original JPG + 1 Horizontal Floor Ledge (0 floating platforms), Contact Shadow (0 ellipses) & Dust FX
  assert.ok(T.state.terrain && T.arena.terrainPlatforms.length === 0, 'Rocky plateau terrain must have 0 floating platforms (1 horizontal floor ledge only)');
  assert.equal(T.state.terrain.backdrop?.mode, 'original_jpg', 'Rocky plateau must preserve original JPG backdrop');
  assert.equal(T.getNearestSupportYBelow(512, 840), 840);
  T.selectCharacter('t_rex');
  T.arena.x = 512;
  T.arena.y = 840;
  T.arena.vy = T.arena.jumpVelocityPxPerMs;
  T.spawnGroundDust(512, 840, 0.9);
  assert.ok(T.arena.dustFx.length >= 1, 'Takeoff must spawn ground dust FX');
  let peakY = 840;
  let landedGround = false;
  for (let tick = 0; tick < 80; tick++) {
    T.stepAndRenderArena(16.67);
    peakY = Math.min(peakY, T.arena.y);
    if (tick > 5 && Math.abs(T.arena.y - 840) < 0.5 && T.arena.vy === 0) {
      landedGround = true;
      break;
    }
  }
  assert.ok(peakY < 760 && landedGround, `Player must jump above ground and land back on horizontal ground_y=840, peak=${peakY} y=${T.arena.y}`);
  assert.equal(getEl('arenaCanvas')._ctx2d._ellipseCalls, 0, 'Pixel contact shadows must never call ctx.ellipse()');

  // Restore default 16:9 profile and fractional mode
  getEl('chkPixelPerfect').onchange({ target: { checked: false } });
  getEl('selDeviceProfile').onchange({ target: { value: 'fhd_16_9' } });
  assert.equal(getEl('arenaCanvas').width, 1920);
  assert.equal(getEl('arenaCanvas').height, 1080);
  tabHumanBtn.click();
}

// Verify ?tab=arena query parameter auto-switches to Tab 2 Arena immediately during initApp()
{
  sandbox.location = { search: '?tab=arena' };
  await T.initApp();
  assert.equal(T.state.activeTab, 'tab-arena', 'URL ?tab=arena must auto-activate Tab 2 on boot');
  tabHumanBtn.click();
}

// Verify progressive asset loading redraws roster avatars, filmstrip, and inspector without staying blank
{
  const chiloAtlas = '/assets/chilopoda/godot_bundle/godot/chilopoda-atlas-00.png';
  delete T.state.images[chiloAtlas];
  delete T.state.imagePromises[chiloAtlas];
  T.renderRosterList();
  T.buildFilmstrip({ frames: [{ duration_ms: 83.33 }], loop: true });
  await T.loadImage(chiloAtlas);
  T.scheduleUiAssetRedraw(true);
  assert.ok(T.state.images[chiloAtlas], 'loadImage must recover unloaded asset and trigger UI refresh');
  assert.equal(getEl('filmstrip').children.length > 0, true, 'Filmstrip must repopulate on asset resolve');
}

// Verify Android APK download controls in header & Tab 2 Arena
{
  assert.ok(html.includes('id="btnDownloadAndroidApkHeader"'), 'Header must expose Android APK download button');
  assert.ok(html.includes('id="btnDownloadAndroidApkArena"'), 'Arena toolbar must expose Android APK download button');
  T.applyAndroidApkInfo({
    available: true,
    filename: 'dr7-studio-debug.apk',
    download_url: '/api/download-android-debug.apk',
    size_mb: 64.8,
    sha256: 'abcdef1234567890',
    built_at_utc: '2026-11-16T07:52:09Z',
  });
  assert.equal(getEl('btnDownloadAndroidApkHeader').href, '/api/download-android-debug.apk');
  assert.ok(getEl('btnDownloadAndroidApkHeader').textContent.includes('64.8 MB'));
  assert.equal(getEl('btnDownloadAndroidApkArena').getAttribute('aria-disabled'), 'false');
  assert.ok(getEl('btnDownloadAndroidApkArena').textContent.includes('64.8 MB'));

  T.applyAndroidApkInfo({ available: false });
  assert.equal(getEl('btnDownloadAndroidApkHeader').getAttribute('aria-disabled'), 'true');
  assert.equal(getEl('btnDownloadAndroidApkArena').getAttribute('aria-disabled'), 'true');
}

console.log('[OK] Frontend E2E + Rust WASM + 2-Tab Dynamic Canvas (Empty Roster + Multi-Character) PASSED 100%!');
