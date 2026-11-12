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

// 3. Load real /api/bundles and /api/benchmarks payloads directly from Python server module
const apiJsonStr = execFileSync(
  'python3',
  [
    '-c',
    `import json, sys; sys.path.insert(0, 'tools/preview'); import server; b=server.discover_bundles(); print(json.dumps({'bundles': b, 'roster': server.load_finalized_roster(b), 'setups': server.build_setups(b), 'parity': server.verify_engine_localhost_parity()}))`,
  ],
  { cwd: REPO_ROOT, encoding: 'utf8' }
);
const apiPayload = JSON.parse(apiJsonStr);
const benchPayload = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'engines/benchmark_report.json'), 'utf8'));

// 4. Execute the entire frontend application inside a Mock DOM + Canvas2D + WASM VM!
function makeMockCtx2d(canvas) {
  let drawCalls = 0;
  return {
    canvas,
    imageSmoothingEnabled: false,
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    font: '',
    filter: 'none',
    get _drawCalls() { return drawCalls; },
    clearRect() {},
    fillRect() { drawCalls++; },
    strokeRect() { drawCalls++; },
    beginPath() {},
    closePath() {},
    moveTo() {},
    lineTo() {},
    stroke() { drawCalls++; },
    fill() { drawCalls++; },
    ellipse() {},
    save() {},
    restore() {},
    translate() {},
    scale() {},
    rotate() {},
    setLineDash() {},
    fillText() { drawCalls++; },
    drawImage() { drawCalls++; },
    createLinearGradient() { return { addColorStop() {} }; },
    getImageData(_x, _y, w, h) {
      return { data: new Uint8ClampedArray(Math.max(1, w) * Math.max(1, h) * 4) };
    },
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
  addEventListener(ev, fn) { (this._listeners[ev] ||= []).push(fn); }
  click() { if (this.onclick) this.onclick({ preventDefault() {}, target: this }); }
}

const elements = new Map();
const getEl = (id) => {
  if (!elements.has(id)) elements.set(id, new MockElement(id));
  return elements.get(id);
};

const tabHumanBtn = new MockElement('', 'BUTTON'); tabHumanBtn.dataset.tab = 'tab-human';
const tabStressBtn = new MockElement('', 'BUTTON'); tabStressBtn.dataset.tab = 'tab-stress';
const tabArenaBtn = new MockElement('', 'BUTTON'); tabArenaBtn.dataset.tab = 'tab-arena';
const tbodyBench = new MockElement('benchTbody', 'TBODY');

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
  performance: { now: () => 1000 },
  setTimeout: () => 1,
  requestAnimationFrame: () => 1,
  navigator: { clipboard: { writeText: async () => {} } },
  Image: class {
    constructor() { this.naturalWidth = 3890; this.naturalHeight = 3382; }
    set src(_u) { if (this.onload) this.onload(); }
  },
  fetch: async (url) => {
    if (url === '/api/bundles') return { ok: true, json: async () => structuredClone(apiPayload) };
    if (url === '/api/benchmarks') return { ok: true, json: async () => structuredClone(benchPayload) };
    if (url === '/rust_combat_sim.wasm') {
      return { ok: true, arrayBuffer: async () => wasmBytes.buffer.slice(wasmBytes.byteOffset, wasmBytes.byteOffset + wasmBytes.byteLength) };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  },
  window: { addEventListener() {} },
  document: {
    createElement: (tag) => new MockElement('', tag.toUpperCase()),
    getElementById: (id) => getEl(id),
    querySelector: (sel) => sel === '#benchCompareTable tbody' ? tbodyBench : getEl(sel),
    querySelectorAll: (sel) => {
      if (sel === '.tab-btn') return [tabHumanBtn, tabStressBtn, tabArenaBtn];
      if (sel === '.tab-view') return [getEl('tab-human'), getEl('tab-stress'), getEl('tab-arena')];
      return [];
    },
  },
};

const instrumentedJs = jsCode + '\n;globalThis.__TEST__ = { initApp, state, stress, arena, selectCharacter, stepInspectorAnimation, renderInspector, stepAndRenderStressArena, stepAndRenderArena, triggerArenaAction, getCanvasSize, getLayerFramesForStep, selectionPixelRuns, updateAgentSpecText, offCtx };';
vm.createContext(sandbox);
vm.runInContext(instrumentedJs, sandbox);

await new Promise(r => setTimeout(r, 60));
const T = sandbox.__TEST__;

assert.equal(getEl('runtimeErrorBanner').textContent, '', 'initApp must produce ZERO runtime errors');

// Phase A: Empty Roster (0 characters) verification on real /api/bundles
if (apiPayload.roster.characters.length === 0) {
  assert.equal(T.state.activeChar, null, 'Empty roster must start with activeChar = null');
  assert.equal(getEl('rosterCountBadge').textContent, '0 Hoàn thiện');
  assert.equal(getEl('clipCountBadge').textContent, '0 clips');
  assert.equal(getEl('arenaCharLabel').textContent, 'Chưa có nhân vật');

  tabStressBtn.click();
  assert.equal(T.state.activeTab, 'tab-stress');
  for (let i = 0; i < 5; i++) {
    T.stepAndRenderStressArena(16.67);
  }
  assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 2 Stress Test with 0 characters must have ZERO runtime errors');
  assert.ok(getEl('stressCanvas')._ctx2d._drawCalls > 2000, 'Tab 2 Stress Canvas must draw all 2,000 Rust WASM entities even when roster is empty');
  assert.match(getEl('kpiAoI').textContent, /\d+ user \(\d+ kbps\)/, 'Tab 2 AoI KPI must report live user count & kbps');

  tabArenaBtn.click();
  T.stepAndRenderArena(16.67);
  assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 3 Arena with 0 characters must have ZERO runtime errors');
  tabHumanBtn.click();
}

// Real assets use the declared body/effect contract; no deleted-character scenarios.
for (const ch of apiPayload.roster.characters) {
  T.selectCharacter(ch.character_id);
  const bundle=T.state.bundlesById[ch.modes.combined_1layer.bundle_id];
  const contract=bundle.render_contract;
  if (!contract) continue;
  const motion=contract.locomotion?.clip||'idle';
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
    assert.equal(T.arena.x,beforeX,'Plant the turn pivot');
    T.triggerArenaAction('attack_light');
    assert.equal(T.arena.clip,contract.turning.clip,'Do not interrupt pending orientation');
    const visited=new Set([T.arena.step]);
    for(let i=0;i<contract.turning.duration_ticks+2;i++){T.stepAndRenderArena(1000/60);if(T.arena.clip===contract.turning.clip)visited.add(T.arena.step);}
    assert.deepEqual([...visited],[0,1,2,3]);
    assert.equal(T.arena.flip,true);
    T.arena.keys={KeyD:true};
    T.stepAndRenderArena(1000/60);
    assert.equal(T.arena.clip,contract.turning.clip);
    assert.equal(T.arena.flip,true);
    for(let i=0;i<contract.turning.duration_ticks+2;i++)T.stepAndRenderArena(1000/60);
    assert.equal(T.arena.flip,false);
    T.arena.keys={};
  }
  T.renderInspector();
  assert.equal(getEl('runtimeErrorBanner').textContent,'');
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

// Test 2: Switch to Tab 2 (>2,000 User Stress Test) with character texture & verify draws + AoI telemetry
tabStressBtn.click();
assert.equal(T.state.activeTab, 'tab-stress');
for (let i = 0; i < 5; i++) {
  T.stepAndRenderStressArena(16.67);
}
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 2 Stress Test must run with ZERO runtime errors');
assert.ok(getEl('stressCanvas')._ctx2d._drawCalls > 2000, 'Tab 2 Stress Canvas must draw all 2,000 fighters');
assert.match(getEl('kpiAoI').textContent, /\d+ user \(\d+ kbps\)/, 'Tab 2 AoI KPI must report live user count & kbps');

// Test 3: Switch to Tab 3 (Sân Tập Gameplay) & verify dynamic skill buttons deal DMG to sparring dummy!
tabArenaBtn.click();
assert.equal(T.state.activeTab, 'tab-arena');
const hpBefore = T.arena.dummyHp;
const burstBtn = getEl('arenaSkillButtons').children.find(b => b.dataset.clip === 'power_up');
assert.ok(burstBtn, 'Tab 3 must dynamically render power_up skill button');
burstBtn.click();
for (let i = 0; i < 6; i++) {
  T.stepAndRenderArena(20.0);
}
assert.equal(T.arena.dummyHp, hpBefore - 250, 'power_up in Tab 3 must deal 250 DMG to dummy');

T.arena.x = 520;
const atkBtn = getEl('arenaSkillButtons').children.find(b => b.dataset.clip === 'attack_light');
assert.ok(atkBtn, 'Tab 3 must dynamically render attack_light skill button');
atkBtn.click();
for (let i = 0; i < 6; i++) {
  T.stepAndRenderArena(20.0);
}
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 3 Gameplay Arena must run with ZERO runtime errors');
assert.equal(T.arena.dummyHp, hpBefore - 250 - 120, 'attack_light at melee range in Tab 3 must deal 120 DMG to dummy');
assert.ok(getEl('arenaCanvas')._ctx2d._drawCalls > 10, 'Tab 3 Arena Canvas must actively draw stage, dummy, and player');

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

console.log('[OK] Frontend E2E + Rust WASM + 3-Tab Dynamic Canvas (Empty Roster + Multi-Character) PASSED 100%!');
