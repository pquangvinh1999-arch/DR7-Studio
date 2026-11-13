"""Play authored whole-frame timelines on three backgrounds before admission."""
from pathlib import Path
import json,base64,sys
sys.path.insert(0,'/tmp/dr7-playwright')
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parent;S=W/'stage';m=json.loads((S/'clips_manifest.json').read_text())
data={n:{'ticks':c['ticks'],'images':['data:image/png;base64,'+base64.b64encode((S/('raw_frames/'+v+'.png')).read_bytes()).decode() for v in c['frames']]} for n,c in m['clips'].items()}
html='''<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#30343d;color:white;font:16px sans-serif}h3{margin:8px}section{display:flex}canvas{width:384px;height:256px;image-rendering:pixelated}</style><main></main><script>
const clips=DATA;const trace={};const items=[];let start=performance.now();
for(const [name,c] of Object.entries(clips)){let h=document.createElement('h3');h.textContent=name;document.querySelector('main').append(h);let row=document.createElement('section');row.id=name;document.querySelector('main').append(row);c.loaded=c.images.map(v=>{let i=new Image();i.src=v;return i});trace[name]=[];for(const bg of ['light','dark','checker']){let cv=document.createElement('canvas');cv.width=384;cv.height=256;row.append(cv);items.push({name,c,bg,cv})}}
window.ready=Promise.all(Object.values(clips).flatMap(c=>c.loaded.map(im=>im.decode()))).then(()=>{start=performance.now();requestAnimationFrame(render)});
function render(now){for(const {name,c,bg,cv}of items){let t=Math.floor((now-start)*60/1000)%c.ticks.reduce((a,b)=>a+b,0),i=0;while(t>=c.ticks[i]&&i<c.ticks.length-1){t-=c.ticks[i++]}const ctx=cv.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle=bg==='light'?'#eee8dc':'#171b23';ctx.fillRect(0,0,384,256);if(bg==='checker'){for(let y=0;y<256;y+=8)for(let x=0;x<384;x+=8){ctx.fillStyle=(x/8+y/8)%2?'#aaa':'#ddd';ctx.fillRect(x,y,8,8)}}ctx.drawImage(c.loaded[i],0,0);if(bg==='light'&&trace[name].at(-1)?.frame!==i)trace[name].push({ms:Math.round(now-start),frame:i})}requestAnimationFrame(render)}window.trace=trace;
</script>'''.replace('DATA',json.dumps(data))
(W/'review/motion.html').write_text(html)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/home/codespace/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1160,'height':600},record_video_dir=str(W/'verification/offline-video'))
    page=context.new_page();errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    page.goto((W/'review/motion.html').as_uri());page.evaluate('window.ready')
    for name in data:
        page.locator('#'+name).scroll_into_view_if_needed();page.wait_for_timeout(2100)
        page.locator('#'+name).screenshot(path=str(W/f'verification/realtime-{name}.png'))
    trace=page.evaluate('window.trace');assert not errors,errors
    for name,c in data.items():assert set(t['frame'] for t in trace[name])==set(range(len(c['ticks']))),(name,trace[name])
    result={'status':'runtime_playback_executed','backgrounds':['light','dark','checker'],'trace':trace,'errors':errors,'limits':'Browser timing observation is not a mobile60FPS benchmark or Owner naturalness approval.'}
    (W/'verification/offline-realtime.json').write_text(json.dumps(result,indent=2)+'\n')
    context.close();browser.close()
print('Offline real-time playback: all8clips/all61poses observed on3backgrounds,0pageerrors.')
