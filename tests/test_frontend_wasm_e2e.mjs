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

// 1. Ensure ZERO hardcoded character bundle IDs & ZERO deprecated 3-layer mode in JS
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

const instrumentedJs = jsCode + '\n;globalThis.__TEST__ = { state, stress, arena, selectCharacter, stepInspectorAnimation, renderInspector, stepAndRenderStressArena, stepAndRenderArena, triggerArenaAction, getCanvasSize };';
vm.createContext(sandbox);
vm.runInContext(instrumentedJs, sandbox);

await new Promise(r => setTimeout(r, 60));
const T = sandbox.__TEST__;

assert.equal(getEl('runtimeErrorBanner').textContent, '', 'initApp must produce ZERO runtime errors');
assert.equal(T.state.activeChar.character_id, 'trunks_rage');
assert.equal(T.state.archMode, 'combined_1layer');
assert.deepEqual(Array.from(T.getCanvasSize()), [320, 256], 'Inspector must dynamically adopt 320x256 canvas from roster.json');
assert.equal(getEl('inspectorCanvas').width, 320 * 2 + 28, 'Inspector canvas at 2x zoom must be 668px wide');
assert.equal(getEl('inspectorCanvas').height, 256 * 2 + 28, 'Inspector canvas at 2x zoom must be 540px high');

// Test 1: Play a oneshot clip ('power_up', 12 frames) with autoReplayOneshot = false until it stops, then click Play!
T.state.activeClipName = 'power_up';
T.state.autoReplayOneshot = false;
T.state.stepIdx = 0;
T.state.stepElapsedMs = 0;
T.state.playing = true;

for (let i = 0; i < 40; i++) {
  T.stepInspectorAnimation(60.0);
}
assert.equal(T.state.playing, false, 'Oneshot clip with autoReplay=false must pause cleanly at final frame');
assert.equal(getEl('btnPlayPause').textContent, '▶ Phát lại từ đầu');

getEl('btnPlayPause').click();
assert.equal(T.state.playing, true, 'Clicking Play after oneshot ends MUST resume playing');
assert.equal(T.state.stepIdx, 0, 'Clicking Play after oneshot ends MUST rewind stepIdx to 0');
T.stepInspectorAnimation(120.0);
assert.ok(T.state.stepIdx >= 1, 'Animation must advance past frame 0 after clicking Play');

// Test 2: Switch to Tab 2 (>2,000 User Stress Test) & verify draws + AoI telemetry + zero crash!
tabStressBtn.click();
assert.equal(T.state.activeTab, 'tab-stress');
for (let i = 0; i < 5; i++) {
  T.stepAndRenderStressArena(16.67);
}
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 2 Stress Test must run with ZERO runtime errors');
assert.ok(getEl('stressCanvas')._ctx2d._drawCalls > 2000, 'Tab 2 Stress Canvas must draw all 2,000 Trunks fighters');
assert.match(getEl('kpiAoI').textContent, /\d+ user \(\d+ kbps\)/, 'Tab 2 AoI KPI must report live user count & kbps');

// Test 3: Switch to Tab 3 (Sân Tập Gameplay) & verify Ultimate Spirit Sword deals 800 DMG to sparring dummy!
tabArenaBtn.click();
assert.equal(T.state.activeTab, 'tab-arena');
const hpBefore = T.arena.dummyHp;
getEl('btnActSpirit').click();
for (let i = 0; i < 6; i++) {
  T.stepAndRenderArena(20.0);
}
assert.equal(getEl('runtimeErrorBanner').textContent, '', 'Tab 3 Gameplay Arena must run with ZERO runtime errors');
assert.equal(T.arena.dummyHp, hpBefore - 800, 'Ultimate Spirit Sword in Tab 3 must deal 800 DMG to dummy');
assert.ok(getEl('arenaCanvas')._ctx2d._drawCalls > 10, 'Tab 3 Arena Canvas must actively draw stage, dummy, and player');

// Test 4: Verify N-Character Roster Scalability (inject 2nd character with custom 288x256 canvas & switch to it!)
const mockChar2 = structuredClone(T.state.api.roster.characters[0]);
mockChar2.character_id = 'vegeta_blue_test_scale';
mockChar2.display_name = 'Vegeta (SSGSS — Test Scale)';
mockChar2.map_sync_metrics.canvas_size_px = [288, 256];
T.state.api.roster.characters.push(mockChar2);
T.selectCharacter('vegeta_blue_test_scale');
assert.equal(T.state.activeChar.character_id, 'vegeta_blue_test_scale');
assert.deepEqual(Array.from(T.getCanvasSize()), [288, 256]);
assert.equal(getEl('rosterList').children.length, 2, 'Roster list must render all N finalized characters');

console.log('[OK] Frontend E2E + Rust WASM + 3-Tab Dynamic Canvas + Trunks 20-Clip Combat PASSED 100%!');
