"""Raster-level burrow visibility, both turn directions, endpoint behavior and actual FX envelope."""
from pathlib import Path
import json,sys,base64,hashlib,urllib.request
sys.path.insert(0,'/tmp/dr7-playwright')
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;V=W/'verification';V.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/home/codespace/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 context=browser.new_context(viewport={'width':1440,'height':1080},record_video_dir=str(V/'burrow-browser-video'))
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://localhost:8080/?character=chilopoda&clip=turn&frame=0&paused=1',wait_until='networkidle')
 page.wait_for_function("state.activeChar?.character_id==='chilopoda' && !!state.wasmExports && Object.keys(state.images).length>0")
 result=page.evaluate('''() => {
 state.playing=false;const b=getCharBundle(),contract=b.render_contract,c=contract.chilopoda;
 const cv=document.createElement('canvas');cv.width=384;cv.height=256;const ctx=cv.getContext('2d',{willReadFrequently:true});
 function sample(clip,tick,options={},bodyOnly=false){const a=b.animations[clip];let i=0,left=tick;while(i<a.frames.length-1&&left>=a.frames[i].duration_ticks)left-=a.frames[i++].duration_ticks;
 const opts={elapsedMs:left*1000/60,fxTicks:0,...options};ctx.clearRect(0,0,384,256);const layers=getLayerFramesForStep(clip,i,opts);
 if(bodyOnly){for(const item of layers.filter(l=>l.layer==='Body')){ctx.save();if(item.clipBelowY!=null){ctx.beginPath();ctx.rect(0,0,384,item.clipBelowY);ctx.clip()}ctx.translate(...item.point);if(item.mirror)ctx.scale(-1,1);const f=item.frame;ctx.drawImage(state.images[f.atlas_url],f.x,f.y,f.w,f.h,-item.pivot[0],-item.pivot[1],384,256);ctx.restore()}}
 else drawCompositeStep(ctx,clip,i,1,1,opts);
 const rgba=ctx.getImageData(0,0,384,256).data;let count=0,x0=384,y0=256,x1=-1,y1=-1;for(let p=3;p<rgba.length;p+=4)if(rgba[p]){const k=(p-3)/4,x=k%384,y=Math.floor(k/384);count++;x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}
 return {tick,frame:i,pixels:count,bbox:count?[x0,y0,x1-x0+1,y1-y0+1]:null,layers:layers.map(l=>({layer:l.layer,point:l.point,mirror:!!l.mirror,angle:l.angle,atlas:[l.frame.x,l.frame.y,l.frame.w,l.frame.h]}))};}
 const attack=Array.from({length:90},(_,t)=>sample('attack_light',t,{},true));const turns=[false,true].map(initialFacingLeft=>({initialFacingLeft,trace:Array.from({length:36},(_,t)=>sample('turn',t,{initialFacingLeft},true))}));
 const envelope=[];for(const clip of contract.body_clips){const total=b.animations[clip].frames.reduce((s,f)=>s+f.duration_ticks,0);for(let tick=0;tick<total;tick++)envelope.push({clip,...sample(clip,tick)})}
 const boxes=envelope.filter(r=>r.bbox).map(r=>r.bbox);let x0=Math.min(...boxes.map(r=>r[0])),y0=Math.min(...boxes.map(r=>r[1])),x1=Math.max(...boxes.map(r=>r[0]+r[2])),y1=Math.max(...boxes.map(r=>r[1]+r[3]));
 const lasers=Array.from({length:42},(_,t)=>sample('power_up',t));
 const boards={};const ticks=[0,3,6,9,12,15,16,21,22,25,28,30,32,34,35];
 for(const initialFacingLeft of [false,true]){const board=document.createElement('canvas');board.width=384*5;board.height=276*3*3;const bc=board.getContext('2d');bc.imageSmoothingEnabled=false;for(const [bi,bg]of ['light','dark','checker'].entries())for(const [j,tick]of ticks.entries()){
 const x=j%5*384,y=(bi*3+Math.floor(j/5))*276;bc.fillStyle=bg==='light'?'#f4f4f4':'#171b23';bc.fillRect(x,y,384,276);if(bg==='checker')for(let py=0;py<256;py+=8)for(let px=0;px<384;px+=8){bc.fillStyle=(px/8+py/8)%2?'#aaa':'#ddd';bc.fillRect(x+px,y+py,8,8)}sample('turn',tick,{initialFacingLeft});bc.drawImage(cv,x,y);bc.fillStyle='#606975';bc.fillRect(x,y+256,384,20);bc.fillStyle='white';bc.font='12px sans-serif';bc.fillText(`${bg} tick ${tick}: ${initialFacingLeft?'left->right':'right->left'}`,x+5,y+270)}boards[initialFacingLeft?'left-to-right':'right-to-left']=board.toDataURL('image/png');}
 return {attack,turns,lasers,envelope,full_fx_bbox_px:{x:x0,y:y0,w:x1-x0,h:y1-y0},boards};}''')
 assert [r['tick'] for r in result['attack'] if r['pixels']==0]==list(range(24,54)),[(r['tick'],r['pixels']) for r in result['attack']]
 for turn in result['turns']:
  assert [r['tick'] for r in turn['trace'] if r['pixels']==0]==list(range(16,22)),turn
  for row in turn['trace']:
   bodies=[l for l in row['layers'] if l['layer']=='Body']
   if bodies:assert bodies[0]['mirror']==(turn['initialFacingLeft']!=(row['tick']>=16)),row
 for direction,data in result.pop('boards').items():(V/f'composite-turn-{direction}.png').write_bytes(base64.b64decode(data.split(',')[1]))
 (V/'burrow-raster-contract.json').write_text(json.dumps(result,indent=2)+'\n')
 sequences=[]
 for bg in ['light','dark','checker']:
  for name in page.evaluate('Object.keys(getCharBundle().animations)'):
   info=page.evaluate('''({name,bg})=>{state.bgMode=bg;state.activeClipName=name;state.stepIdx=0;state.stepElapsedMs=0;state.fxTicks=0;state.autoReplayOneshot=false;state.playing=true;state.showBBox=false;state.showMapGrid=false;syncClipChoices();window.motionTrace=[];window.motionRun=(window.motionRun||0)+1;const run=window.motionRun;let last=-1,base=performance.now();window.motionStop=false;function observe(now){if(run!==window.motionRun)return;if(state.stepIdx!==last){motionTrace.push({ms:Math.round(now-base),frame:state.stepIdx});last=state.stepIdx}if(!motionStop)requestAnimationFrame(observe)}requestAnimationFrame(observe);const a=getActiveTimelineFrames();return {frames:a.frames.length,total:a.frames.reduce((s,f)=>s+f.duration_ms,0),loop:a.loop}}''',{'name':name,'bg':bg})
   page.wait_for_timeout(info['total']*(2 if info['loop'] else 1)+120)
   if not info['loop']:page.wait_for_function('!state.playing',timeout=5000)
   obs=page.evaluate('''()=>{motionStop=true;return {trace:motionTrace,final:state.stepIdx,playing:state.playing}}''')
   if not info['loop']:assert obs['final']==info['frames']-1 and not obs['playing'],(name,obs)
   observed={r['frame'] for r in obs['trace']};sequences.append({'clip':name,'background':bg,'info':info,'observation':obs,'unobserved_frames':sorted(set(range(info['frames']))-observed)})
  page.evaluate("state.activeClipName='turn';state.playing=false;state.stepIdx=5;state.stepElapsedMs=30;syncClipChoices();renderInspector()")
  page.locator('#inspectorCanvas').screenshot(path=str(V/f'browser-turn-{bg}.png'))
 page.screenshot(path=str(V/'browser-workbench-turn.png'),full_page=True)
 assert not errors,errors
 (V/'browser-realtime-turn.json').write_text(json.dumps({'sequences':sequences,'errors':errors,'limits':'Observed headless browser playback, not a mobile60FPS benchmark. Missed poses are reported, not inferred.'},indent=2)+'\n')
 context.close();browser.close()
print(json.dumps({'attack_hidden_ticks':30,'turn_hidden_ticks':6,'turn_directions':2,'full_fx_bbox_px':result['full_fx_bbox_px'],'browser_sequences':len(sequences),'errors':errors,'unobserved_frames':sum(len(r['unobserved_frames']) for r in sequences)}))
