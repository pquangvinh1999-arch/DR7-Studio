"""Live localhost inspector playback plus deterministic40tick mouth/FX contract."""
import json,sys,hashlib,urllib.request
from pathlib import Path
sys.path.insert(0,'/tmp/dr7-playwright')
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;R=W.parents[3];V=W/'verification'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/home/codespace/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':1440,'height':1080},record_video_dir=str(V/'browser-video'))
    page=context.new_page();errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    page.goto('http://localhost:8080/?character=bat_chiroptera&clip=power_up&frame=0&paused=1',wait_until='networkidle')
    page.wait_for_function("state.activeChar?.character_id==='bat_chiroptera' && !!state.wasmExports")
    trace=page.evaluate('''() => {const b=getCharBundle();const a=b.animations.power_up;const result=[];for(let t=0;t<40;t++){let index=0,left=t;while(left>=a.frames[index].duration_ticks&&index<a.frames.length-1)left-=a.frames[index++].duration_ticks;let layers=getLayerFramesForStep('power_up',index,{elapsedMs:left*1000/60,fxTicks:0});result.push({tick:t,body:index,layers:layers.map(l=>({layer:l.layer,point:l.point||null,pivot:l.pivot||null,rect:[l.frame.x,l.frame.y,l.frame.w,l.frame.h]}))})}return result}''')
    for row in trace:
        fx=[l for l in row['layers'] if l['layer']=='Projectile']
        assert bool(fx)==(10<=row['tick']<24),row
        if fx:assert fx[0]['point']==[225,165] and fx[0]['pivot']==[176,141],row
    sequences=[]
    names=page.evaluate('Object.keys(getCharBundle().animations)')
    for bg in ['light','dark','checker']:
        for name in names:
            info=page.evaluate('''({bg,name})=>{state.bgMode=bg;state.activeClipName=name;state.stepIdx=0;state.stepElapsedMs=0;state.fxTicks=0;state.autoReplayOneshot=false;state.playing=true;state.showBBox=false;state.showMapGrid=false;syncClipChoices();window.batTrace=[];let last=-1,base=performance.now();window.batStop=false;function observe(now){if(state.stepIdx!==last){batTrace.push({ms:Math.round(now-base),frame:state.stepIdx});last=state.stepIdx}if(!batStop)requestAnimationFrame(observe)}requestAnimationFrame(observe);return {frames:getActiveTimelineFrames().frames.length,total:getActiveTimelineFrames().frames.reduce((s,f)=>s+f.duration_ms,0),loop:getActiveTimelineFrames().loop}}''',{'bg':bg,'name':name})
            page.wait_for_timeout(info['total']*(2 if info['loop'] else 1)+180)
            observation=page.evaluate('''()=>{batStop=true;return {trace:batTrace,final:state.stepIdx,playing:state.playing}}''')
            assert observation['final']<info['frames'],observation
            if not info['loop']:assert observation['final']==info['frames']-1 and not observation['playing'],(name,observation)
            observed=set(r['frame'] for r in observation['trace'])
            sequences.append({'clip':name,'background':bg,'info':info,'observation':observation,'unobserved_frames':sorted(set(range(info['frames']))-observed)})
        page.evaluate("state.activeClipName='power_up';state.playing=false;state.stepIdx=2;state.stepElapsedMs=0;state.fxTicks=0;syncClipChoices();renderInspector()")
        page.locator('#inspectorCanvas').screenshot(path=str(V/f'browser-sonic-{bg}.png'))
    page.screenshot(path=str(V/'browser-workbench.png'),full_page=True)
    assert not errors,errors
    (V/'browser-realtime.json').write_text(json.dumps({'sequences':sequences,'errors':errors,'limits':'Observed browser playback, not a mobile60FPS benchmark. Unobserved poses reported per sequence rather than inferred.'},indent=2)+'\n')
    (V/'browser-power40tick.json').write_text(json.dumps(trace,indent=2)+'\n')
    context.close();browser.close()
payload=json.load(urllib.request.urlopen('http://localhost:8080/api/bundles'));assert payload['parity']['ok'],payload['parity']
hashes={}
for rel,url in [('assets/bat_chiroptera/godot_bundle/godot/bat_chiroptera-atlas-00.png','/assets/bat_chiroptera/godot_bundle/godot/bat_chiroptera-atlas-00.png'),('tools/preview/rust_combat_sim.wasm','/rust_combat_sim.wasm')]:
    local=hashlib.sha256((R/rel).read_bytes()).hexdigest();remote=hashlib.sha256(urllib.request.urlopen('http://localhost:8080'+url).read()).hexdigest();assert local==remote;hashes[rel]={'local':local,'http':remote}
(V/'http-byte-parity.json').write_text(json.dumps({'parity':payload['parity'],'hashes':hashes,'motion_quality':payload['motion_quality']['characters']['bat_chiroptera']},indent=2)+'\n')
print(json.dumps({'sequences':len(sequences),'errors':len(errors),'deterministic_power_ticks':len(trace),'http_hash_parity':True,'unobserved_frames':sum(len(s['unobserved_frames']) for s in sequences)}))
