/* global process, setTimeout, fetch, WebSocket, Buffer, console */
import { spawn } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { tmpdir } from 'node:os'

const chromePath = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const output = resolve('docs/visual/phase5_1_current')
const profile = resolve(tmpdir(), `civisar-chrome-visual-${process.pid}`)
const port = 9227
const viewports = [[1440, 900], [1366, 768], [1024, 768], [768, 1024], [390, 844]]
const views = ['main', 'alert', 'area', 'brief', 'routes', 'shelters', 'inspect', 'sources', 'signin', 'phone']
const routes = {main:'/',alert:'/alerts',area:'/areas',brief:'/brief',routes:'/routes',shelters:'/shelters',inspect:'/inspector',sources:'/sources',signin:'/signin',phone:'/phone'}
const sleep = ms => new Promise(done => setTimeout(done, ms))

async function connect() {
  for (let attempt=0; attempt<40; attempt++) {
    try { const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (pages[0]) return pages[0].webSocketDebuggerUrl } catch { /* Chrome starting */ }
    await sleep(250)
  }
  throw new Error('Chrome DevTools endpoint did not start')
}

async function main() {
  await mkdir(output, {recursive:true})
  const chrome = spawn(chromePath, ['--headless=new','--no-first-run','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader',`--user-data-dir=${profile}`,`--remote-debugging-port=${port}`,'--remote-allow-origins=*','about:blank'], {stdio:'ignore',windowsHide:true})
  try {
    const url = await connect()
    const socket = new WebSocket(url)
    await new Promise((done,fail) => {socket.addEventListener('open',done,{once:true});socket.addEventListener('error',fail,{once:true})})
    let sequence=0
    const pending = new Map()
    socket.addEventListener('message', event => {const msg=JSON.parse(event.data);if(msg.method==='Runtime.consoleAPICalled'&&msg.params.type==='error')console.error('Browser:',msg.params.args.map(x=>x.value||x.description).join(' '));if(!msg.id)return;const p=pending.get(msg.id);if(!p)return;pending.delete(msg.id);if(msg.error)p.fail(new Error(msg.error.message));else p.done(msg.result)})
    const send=(method,params={})=>new Promise((done,fail)=>{const id=++sequence;pending.set(id,{done,fail});socket.send(JSON.stringify({id,method,params}))})
    const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value}
    await send('Page.enable')
    await send('Runtime.enable')
    await send('Network.enable')
    for (const [width,height] of viewports.filter(([w,h])=>!process.env.CIVISAR_VISUAL_SIZE || `${w}x${h}`===process.env.CIVISAR_VISUAL_SIZE)) {
      await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false})
      for (const view of views.filter(v=>!process.env.CIVISAR_VISUAL_ONLY || process.env.CIVISAR_VISUAL_ONLY.split(',').includes(v))) {
        await send('Page.navigate',{url:`http://127.0.0.1:4174/civisar-prototype.html?capture=${width}-${height}-${view}#${view}`})
        await sleep(900)
        const location=await evaluate('location.href')
        if (!location.includes('civisar-prototype.html')) throw new Error(`Reference navigation failed: ${location}`)
        let opened=false
        for(let attempt=0;attempt<20;attempt++){opened=await evaluate(`document.querySelector('#v-${view}')?.hidden === false`);if(opened)break;await sleep(250)}
        if (!opened) throw new Error(`Reference view ${view} did not open: ${await evaluate('document.body?.innerText?.slice(0,120)')}`)
        await evaluate('document.fonts.ready.then(()=>true)')
        await sleep(250)
        const reference=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})
        await writeFile(resolve(output,`prototype-${view}-${width}x${height}-light.png`),Buffer.from(reference.data,'base64'))
        if(view==='main'){
          for(const panel of ['layers','alerts']){
            await evaluate(`document.querySelector('#v-main .dock [data-p=${panel}]').click()`)
            await sleep(150)
            const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})
            await writeFile(resolve(output,`prototype-main-${panel}-${width}x${height}-light.png`),Buffer.from(shot.data,'base64'))
            await evaluate(`document.querySelector('#v-main .dock [data-p=${panel}]').click()`)
          }
        }
        await send('Network.clearBrowserCookies')
        await send('Page.navigate',{url:`http://127.0.0.1:5173${routes[view]}`})
        await sleep(900)
        if (process.env.CIVISAR_VISUAL_USERNAME && process.env.CIVISAR_VISUAL_PASSWORD && view!=='signin') {
          await evaluate(`fetch('/api/v1/session',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({username:${JSON.stringify(process.env.CIVISAR_VISUAL_USERNAME)},password:${JSON.stringify(process.env.CIVISAR_VISUAL_PASSWORD)}})}) .then(r=>r.ok)`)
          await send('Page.navigate',{url:`http://127.0.0.1:5173${routes[view]}`})
          await sleep(view==='main'?5000:1100)
        }
        const actualPath=await evaluate('location.pathname')
        if(actualPath!==routes[view]) throw new Error(`React route mismatch for ${view}: ${actualPath}`)
        await evaluate('document.fonts.ready.then(()=>true)')
        const app=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})
        await writeFile(resolve(output,`react-${view}-${width}x${height}-light.png`),Buffer.from(app.data,'base64'))
        if(view==='main'&&width===1440) console.log('Map geometry:',await evaluate(`(()=>{const c=document.querySelector('.prototype-main canvas');return JSON.stringify({map:document.querySelector('.prototype-main .map')?.getBoundingClientRect().toJSON(),canvas:c?.getBoundingClientRect().toJSON(),webgl2:!!c?.getContext('webgl2'),webgl:!!c?.getContext('webgl'),fallback:document.querySelector('.map-fallback')?.textContent})})()`))
        if(view==='main'){
          for(const panel of ['Layers','Alerts']){
            await evaluate(`Array.from(document.querySelectorAll('#v-main .dock button')).find(b=>b.textContent.includes('${panel}')).click()`)
            await sleep(150)
            const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false})
            await writeFile(resolve(output,`react-main-${panel.toLowerCase()}-${width}x${height}-light.png`),Buffer.from(shot.data,'base64'))
            await evaluate(`Array.from(document.querySelectorAll('#v-main .dock button')).find(b=>b.textContent.includes('${panel}')).click()`)
          }
        }
      }
    }
    await writeFile(resolve(output,'compare.html'), `<!doctype html><meta charset="utf-8"><title>CIVISAR visual pairs</title><style>body{font:14px system-ui;background:#222;color:white;margin:16px}select,input{font:inherit;margin:6px}main{position:relative;width:max-content;max-width:100%}img{display:block;max-width:100%;height:auto}#react{position:absolute;top:0;left:0;opacity:.5}small{display:block;margin:8px 0}</style><h1>Prototype / React overlay</h1><label>View <select id="view">${views.map(v=>`<option>${v}</option>`).join('')}</select></label><label>Viewport <select id="size">${viewports.map(([w,h])=>`<option>${w}x${h}</option>`).join('')}</select></label><label>React opacity <input id="blend" type="range" min="0" max="100" value="50"></label><small>Prototype base; React overlay. Match is assessed by visual review, not by the presence of screenshots.</small><main><img id="prototype" alt="Original prototype"><img id="react" alt="React implementation"></main><script>function update(){const suffix=window.view.value+'-'+window.size.value+'-light.png';window.prototype.src='prototype-'+suffix;window.react.src='react-'+suffix;window.react.style.opacity=window.blend.value/100}for(const id of ['view','size','blend'])window[id].addEventListener('input',update);update()</script>`)
    socket.close()
  } finally {chrome.kill()}
}
main().catch(error=>{console.error(error);process.exitCode=1})
