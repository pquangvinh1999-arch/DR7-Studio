"""Actual browser endpoint traces and downloadable Godot-pack integrity."""
from pathlib import Path
import json,sys,hashlib,urllib.request,zipfile,io
sys.path.insert(0,'/tmp/dr7-playwright')
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;R=W.parents[3];V=W/'verification'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/home/codespace/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 context=browser.new_context(viewport={'width':1440,'height':1080},record_video_dir=str(V/'endpoint-browser-video'))
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://localhost:8080/?character=chilopoda&clip=turn&frame=0&paused=1',wait_until='networkidle');page.wait_for_function("state.activeChar?.character_id==='chilopoda' && !!state.wasmExports")
 trace=page.evaluate('''()=>{state.playing=false;selectCharacter('chilopoda');Object.assign(arena,{x:879,flip:false,keys:{KeyD:true},hitstop:0,actionClip:null,turnTargetFlip:null,chiloPatrol:false,chiloAction:null,dummyHp:2000});const b=getCharBundle(),result=[];
 function row(endpoint){const anim=b.animations[arena.clip],tick=animationFrameTick(anim,arena.step)+arena.elapsed*.06;return {endpoint,clip:arena.clip,frame:arena.step,tick,x:arena.x,flip:arena.flip,patrolDirection:arena.chiloPatrolDir,bodyVisible:chilopodaActionState(b.render_contract,arena.clip,tick).bodyVisible}}
 for(let t=0;t<40;t++){stepAndRenderArena(1000/60);result.push(row('right'))}
 Object.assign(arena,{x:81,keys:{}});for(let t=0;t<40;t++){stepAndRenderArena(1000/60);result.push(row('left'))}return result}''')
 for endpoint,initial in [('right',False),('left',True)]:
  rows=[r for r in trace if r['endpoint']==endpoint];turn=[r for r in rows if r['clip']=='turn'];assert turn
  assert all(abs(r['x']-(880 if endpoint=='right' else 80))<.001 for r in turn),turn
  changed=next(r for r in turn if r['flip']!=initial);assert 16<=changed['tick']<22 and not changed['bodyVisible'],changed
  assert rows[-1]['clip']=='walk' and rows[-1]['flip']!=initial,rows[-1]
  assert rows[-1]['patrolDirection']==(-1 if endpoint=='right' else 1)
 assert not errors,errors
 (V/'browser-endpoints.json').write_text(json.dumps({'trace':trace,'errors':errors,'limits':'Deterministic60Hz calls in real Chromium Canvas/runtime; observed wall-clock playback is recorded separately.'},indent=2)+'\n')
 # Capture the Arena after the deterministic endpoint trace.
 page.locator('[data-tab="tab-arena"]').click()
 page.screenshot(path=str(V/'browser-arena-endpoint.png'),full_page=True)
 context.close();browser.close()
payload=json.load(urllib.request.urlopen('http://localhost:8080/api/bundles'));assert payload['parity']['ok'],payload['parity'];assert payload['motion_quality']['characters']['chilopoda']['ok_for_human_test'];assert not payload['motion_quality']['characters']['chilopoda']['release_approved']
hashes={}
for rel,url in [('assets/chilopoda/godot_bundle/godot/chilopoda-atlas-00.png','/assets/chilopoda/godot_bundle/godot/chilopoda-atlas-00.png'),('tools/preview/rust_combat_sim.wasm','/rust_combat_sim.wasm')]:
 local=hashlib.sha256((R/rel).read_bytes()).hexdigest();remote=hashlib.sha256(urllib.request.urlopen('http://localhost:8080'+url).read()).hexdigest();assert local==remote;hashes[rel]={'local':local,'http':remote}
packed=urllib.request.urlopen('http://localhost:8080/api/download-godot-pack.zip',timeout=120).read();(V/'godot-pack-turn.zip').write_bytes(packed)
with zipfile.ZipFile(io.BytesIO(packed)) as z:
 assert z.testzip() is None
 compared=[]
 for name in z.namelist():
  if name.startswith('assets/chilopoda/godot_bundle/') or name in ['scenes/Chilopoda.tscn','scenes/ChilopodaFighter2D.gd','scenes/ChilopodaGroundClip.gdshader','assets/roster.json']:
   assert z.read(name)==(R/name).read_bytes(),name;compared.append(name)
 out=V/'standalone-godot-turn';assert not out.exists(),'Use a fresh ZIP verification directory';z.extractall(out)
(V/'delivery-parity-turn.json').write_text(json.dumps({'hashes':hashes,'http_parity':payload['parity'],'motion_quality':payload['motion_quality']['characters']['chilopoda'],'zip_crc':'ok','zip_compared_files':compared,'zip_sha256':hashlib.sha256(packed).hexdigest(),'zip_extracted':str(out.relative_to(R))},indent=2)+'\n')
print(json.dumps({'browser_endpoints':2,'errors':errors,'http_hashes_equal':True,'zip_crc':'ok','zip_compared_files':len(compared),'zip_bytes':len(packed)}))
