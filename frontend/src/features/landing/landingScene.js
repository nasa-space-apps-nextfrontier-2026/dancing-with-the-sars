// RescueForce landing scene: three.js Earth, scroll-driven dive to Khiam, fire and smoke, cards and reveals.
// Ported from docs/design/rescueforce-landing-mockup.html. Plain JS on purpose (DOM-heavy scene code);
// typed entry point in landingScene.d.ts.
import * as THREE from 'three'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'

gsap.registerPlugin(ScrollTrigger)

/** Starts the scene inside `root`. `navigate(path)` routes in-app links. Returns a cleanup function. */
export function initLanding(root, navigate) {
  const cleanups = []
  let alive = true, rafId = 0
  // in-app links (Try RescueForce, Open RescueForce) go to the dashboard without a page reload
  root.querySelectorAll('a[data-link]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); navigate(a.getAttribute('href')) }))
  const ctx = gsap.context(() => {
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';   // the story always starts on the globe
    if (!location.hash) window.scrollTo(0, 0);
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const $ = s => root.querySelector(s);
    const clamp = (v, a=0, b=1) => Math.min(b, Math.max(a, v));
    const ease = t => t<.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2;
    const range = (p, a, b) => clamp((p - a) / (b - a));
    const esri = (bbox, w, h) => `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=${bbox}&bboxSR=4326&imageSR=4326&size=${w},${h}&format=jpg&f=image`;
    const distM = (a, b) => Math.hypot((a.lon-b.lon)*111320*Math.cos(a.lat*Math.PI/180), (a.lat-b.lat)*111320);

    /* =================== geography (sample data from the dashboard) =================== */
    const BB = {w:35.15, e:35.75, s:33.02, n:33.42};                 // regional image (56 x 44 km)
    const HB = {w:35.600, e:35.640, s:33.318, n:33.342};              // close-up tile over Khiam (3.7 x 2.7 km)
    const HW = 2048, HH = 1465;
    const KHIAM = {lon:35.6195, lat:33.3305};
    const INC = [
      {name:'Khiam east', rank:1, lon:35.6195, lat:33.3305, c:'var(--dmg-severe)'},
      {name:'Bint Jbeil centre', rank:2, lon:35.4335, lat:33.1205, c:'var(--dmg-destroyed)'},
      {name:'Aitaroun south', rank:3, lon:35.4705, lat:33.1135, c:'var(--dmg-moderate)'},
      {name:'Nabatieh al-Fawqa', rank:4, lon:35.4985, lat:33.3775, c:'var(--dmg-possible)'},
    ];
    const DMG = [ // candidate damaged buildings around Khiam (size in metres)
      {lon:35.6188, lat:33.3311, m:45, c:'#f5904f'}, {lon:35.6201, lat:33.3302, m:40, c:'#ff7a93'},
      {lon:35.6212, lat:33.3296, m:50, c:'#f2b84b'}, {lon:35.6179, lat:33.3292, m:35, c:'#eadf73'},
    ];
    const FIRES = [{lon:35.6199, lat:33.3306, big:1}, {lon:35.6213, lat:33.3294, big:.7}];
    const SHELTERS = [
      {name:'Sample shelter 1', lon:35.6105, lat:33.3372},
      {name:'Sample shelter 3', lon:35.6150, lat:33.3345},
    ];
    const ROUTES = [ // available road and the ridge road near damage (endpoints; drawn as sample straight lines)
      {id:'west', a:[35.6060,33.3390], b:[35.6190,33.3308], label:'Western road', blocked:false},
      {id:'ridge', a:[35.6168,33.3289], b:[35.6245,33.3283], label:'Ridge road', blocked:true},
      {id:'sh1', a:[35.6195,33.3305], b:[35.6105,33.3372], label:'To shelter', blocked:false, shelter:true},
    ];

    /* =================== bird view plane =================== */
    const plane = $('#plane'), hires = $('#hires');
    plane.style.backgroundImage = `url("${esri(`${BB.w},${BB.s},${BB.e},${BB.n}`, 1600, 1270)}")`;
    const toPlane = (lon, lat) => ({x:(lon-BB.w)/(BB.e-BB.w), y:(BB.n-lat)/(BB.n-BB.s)});   // 0..1
    const toTile  = (lon, lat) => ({x:(lon-HB.w)/(HB.e-HB.w), y:(HB.n-lat)/(HB.n-HB.s)});
    const kp = toPlane(KHIAM.lon, KHIAM.lat);
    plane.style.setProperty('--ox', (kp.x*100)+'%'); plane.style.setProperty('--oy', (kp.y*100)+'%');
    plane.style.setProperty('--fx', (-kp.x).toFixed(4)); plane.style.setProperty('--fy', (-kp.y).toFixed(4));
    // sharp close-up tile, placed exactly over its lon/lat box on the regional image
    const t0 = toPlane(HB.w, HB.n), t1 = toPlane(HB.e, HB.s);
    Object.assign(hires.style, {left:(t0.x*100)+'%', top:(t0.y*100)+'%', width:((t1.x-t0.x)*100)+'%', height:((t1.y-t0.y)*100)+'%',
      backgroundImage:`url("${esri(`${HB.w},${HB.s},${HB.e},${HB.n}`, HW, HH)}")`});

    // anchors: zero-size points on the ground; screen-space markers follow them every frame
    function anchor(lon, lat){
      const inTile = lon>=HB.w && lon<=HB.e && lat>=HB.s && lat<=HB.n, host = inTile ? hires : plane;
      const p = inTile ? toTile(lon, lat) : toPlane(lon, lat), a = document.createElement('i');
      a.className = 'anchor'; a.style.left = (p.x*100)+'%'; a.style.top = (p.y*100)+'%'; host.appendChild(a); return a;
    }

    // regional overlay: small hatched areas at each incident
    const NS = 'http://www.w3.org/2000/svg';
    const svgAdd = (root, tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); root.appendChild(e); return e; };
    const ov = $('#overlay');
    INC.forEach(i => { const p = toPlane(i.lon, i.lat); svgAdd(ov, 'circle', {cx:p.x*1600, cy:p.y*1270, r:9, fill:'none', stroke:'#fff', 'stroke-opacity':.5, 'stroke-width':.8, class:'regdot'}); });

    // close-up overlay (tile coordinates): damage footprints, pulse rings, fire rings, routes
    const hov = $('#hov'); hov.setAttribute('viewBox', `0 0 ${HW} ${HH}`);
    const tpx = (lon, lat) => { const p = toTile(lon, lat); return {x:p.x*HW, y:p.y*HH}; };
    const mPerPx = distM({lon:HB.w, lat:33.33}, {lon:HB.e, lat:33.33}) / HW;      // ≈ 1.8 m per tile pixel
    hov.innerHTML = `<defs>
      <pattern id="hz" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.2" height="9" fill="#fff"/></pattern>
      <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <g id="g-routes"></g><g id="g-rings"></g><g id="g-dmg"></g>`;
    const gR = hov.querySelector('#g-routes'), gRing = hov.querySelector('#g-rings'), gD = hov.querySelector('#g-dmg');
    FIRES.forEach(f => { const p = tpx(f.lon, f.lat); svgAdd(gRing, 'circle', {cx:p.x, cy:p.y, r:375/mPerPx, fill:'rgba(255,138,77,.05)', stroke:'#ff8a4d', 'stroke-width':3, 'stroke-dasharray':'14 9', class:'z-ring'}); });
    DMG.forEach((d, i) => {
      const p = tpx(d.lon, d.lat), s = d.m/mPerPx, g = svgAdd(gD, 'g', {class:'z-dmg'});
      svgAdd(g, 'rect', {x:p.x-s/2, y:p.y-s/2, width:s, height:s, rx:3, fill:d.c, 'fill-opacity':.32});
      const out = svgAdd(g, 'rect', {x:p.x-s/2, y:p.y-s/2, width:s, height:s, rx:3, fill:'none', stroke:d.c, 'stroke-width':5, filter:'url(#glow)'});
      out.innerHTML = `<animate attributeName="stroke-opacity" values="1;.35;1" dur="${1.6+i*.2}s" repeatCount="indefinite"/>`;
      const pr = svgAdd(g, 'circle', {cx:p.x, cy:p.y, r:s*.7, fill:'none', stroke:d.c, 'stroke-width':2.5});
      pr.innerHTML = `<animate attributeName="r" values="${s*.6};${s*2.2}" dur="2.4s" begin="${i*.5}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".9;0" dur="2.4s" begin="${i*.5}s" repeatCount="indefinite"/>`;
    });
    // proper diagonal hatching per footprint (pattern clipped to each square, in its own colour)
    DMG.forEach((d, i) => {
      const p = tpx(d.lon, d.lat), s = d.m/mPerPx;
      const pat = svgAdd(hov.querySelector('defs'), 'pattern', {id:'hp'+i, width:8, height:8, patternUnits:'userSpaceOnUse', patternTransform:'rotate(45)'});
      svgAdd(pat, 'rect', {width:3, height:8, fill:d.c});
      svgAdd(gD, 'rect', {x:p.x-s/2, y:p.y-s/2, width:s, height:s, rx:3, fill:`url(#hp${i})`, 'fill-opacity':.85, class:'z-dmg'});
    });

    /* routes: sample lines between the endpoints (no public routing server is called; doc 03/07);
       parts near damage turn red ("may be blocked") */
    const routeEls = [];
    function drawRoute(r, coords){
      const pts = coords.map(([lon, lat]) => ({lon, lat}));
      const near = pts.map(q => DMG.some(d => distM(d, q) <= d.m/2 + 40));
      const toD = arr => arr.map((q, i) => { const p = tpx(q.lon, q.lat); return (i?'L':'M')+p.x.toFixed(1)+' '+p.y.toFixed(1); }).join(' ');
      const all = toD(pts);
      svgAdd(gR, 'path', {d:all, fill:'none', stroke:'#05070a', 'stroke-opacity':.65, 'stroke-width':r.shelter?13:17, 'stroke-linecap':'round', 'stroke-linejoin':'round', class:'z-route'});
      // split into clear / near-damage runs
      let run = [pts[0]], f = near[0] || near[1];
      const flush = (arr, red) => { if (arr.length < 2) return;
        const el = svgAdd(gR, 'path', {d:toD(arr), fill:'none', 'stroke-linecap':'round', 'stroke-linejoin':'round', class:'z-route',
          stroke: red || r.blocked ? '#ff5a5f' : '#f1f4f3', 'stroke-width': r.shelter ? 6 : 8, 'stroke-dasharray': red || r.blocked ? '18 11' : (r.shelter ? '14 9' : 'none')});
        routeEls.push(el); };
      for (let i = 1; i < pts.length; i++) { const nf = near[i-1] || near[i]; if (nf !== f) { flush(run, f); run = [pts[i-1]]; f = nf; } run.push(pts[i]); }
      flush(run, f);
      const mid = pts[Math.floor(pts.length * (r.blocked ? .5 : .35))];
      return {mid, touches: r.blocked || near.some(Boolean)};
    }
    const routeInfo = {};
    ROUTES.forEach(r => { routeInfo[r.id] = drawRoute(r, [r.a, r.b]); });                      // sample straight lines

    /* =================== screen-space markers =================== */
    const fx = $('#fx'), markers = [];
    function marker(lon, lat, cls, html, group){
      const el = document.createElement('div'); el.className = 'mk ' + cls; el.innerHTML = `<div class="in">${html}</div>`;
      fx.appendChild(el); const m = {el, a:anchor(lon, lat), group}; markers.push(m); return m;
    }
    // regional: four ranked incidents
    INC.forEach(i => marker(i.lon, i.lat, '', `<span class="pill">${i.name}</span><b class="rk" style="--c:${i.c}">${i.rank}</b><span class="stem" style="--c:${i.c}"></span>`, 'reg'));
    // close-up: incident, shelters, damage and fire labels
    marker(KHIAM.lon, KHIAM.lat + .0011, '', `<span class="pill">Khiam east<small>Heavy damage likely · candidate</small></span><b class="rk" style="--c:var(--dmg-severe)">1</b><span class="stem" style="--c:var(--dmg-severe)"></span>`, 'zoom');
    SHELTERS.forEach(s => marker(s.lon, s.lat, 'shelter', `<span class="pill">${s.name}<small>Shelter option · not verified</small></span><span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f1f4f3" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/></svg></span><span class="stem" style="--c:#f1f4f3"></span>`, 'zoom'));
    marker(35.6176, 33.3286, 'tagmk dmg', `<span class="pill">Damaged buildings · candidate</span>`, 'zoom');
    marker(FIRES[0].lon + .0016, FIRES[0].lat + .0009, 'tagmk fire', `<span class="pill">Fire · illustrative effect</span>`, 'zoom');
    const routeTags = [];
    function placeRouteTags(){
      routeTags.forEach(m => { m.el.remove(); m.a.remove(); markers.splice(markers.indexOf(m), 1); }); routeTags.length = 0;
      const w = routeInfo.west, rd = routeInfo.ridge;
      if (w) routeTags.push(marker(w.mid.lon, w.mid.lat, 'tagmk', `<span class="pill">Open route · not checked</span>`, 'zoom'));
      if (rd) routeTags.push(marker(rd.mid.lon, rd.mid.lat - .0006, 'tagmk red', `<span class="pill">May be blocked · candidate</span>`, 'zoom'));
      routeTags.forEach(m => { m.el.style.opacity = groupOpacity.zoom; });
    }
    const groupOpacity = {reg:0, zoom:0};
    placeRouteTags();

    /* =================== fire and smoke (canvas particles, illustrative) =================== */
    const fc = $('#fire'), fctx = fc.getContext('2d');
    const fireAnchors = FIRES.map(f => ({a:anchor(f.lon, f.lat), big:f.big}));
    function sprite(stops, size=128){ const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d');
      const gr = g.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2); stops.forEach(([o, col]) => gr.addColorStop(o, col)); g.fillStyle = gr; g.fillRect(0, 0, size, size); return c; }
    const SP = {
      core:  sprite([[0,'rgba(255,255,235,1)'],[.25,'rgba(255,236,170,.95)'],[.6,'rgba(255,170,60,.35)'],[1,'rgba(255,120,30,0)']], 64),
      flame: sprite([[0,'rgba(255,214,130,1)'],[.3,'rgba(255,150,50,.85)'],[.65,'rgba(230,70,18,.4)'],[1,'rgba(200,40,10,0)']]),
      red:   sprite([[0,'rgba(255,120,50,.9)'],[.5,'rgba(200,50,15,.45)'],[1,'rgba(150,20,5,0)']]),
      ember: sprite([[0,'rgba(255,250,215,1)'],[.35,'rgba(255,170,70,.95)'],[1,'rgba(255,90,20,0)']], 32),
      smoke: sprite([[0,'rgba(48,45,42,.9)'],[.45,'rgba(52,49,46,.55)'],[1,'rgba(50,50,50,0)']]),
      glow:  sprite([[0,'rgba(255,150,60,.65)'],[.35,'rgba(255,110,40,.28)'],[1,'rgba(255,80,20,0)']], 256),
    };
    const parts = [];
    let fireAmt = 0, emitAcc = new Map();
    function emit(src, kind, n){
      for (let i = 0; i < n; i++){
        const r = Math.random;
        if (kind === 'flame') parts.push({src, k:'flame', x:(r()-.5)*14*src.big, h:r()*3, vx:(r()-.5)*2, vh:7+r()*9, age:0, life:.55+r()*.7, s:(9+r()*10)*src.big});
        else if (kind === 'core') parts.push({src, k:'core', x:(r()-.5)*7*src.big, h:0, vx:0, vh:5+r()*6, age:0, life:.35+r()*.4, s:(5+r()*4)*src.big});
        else if (kind === 'ember') parts.push({src, k:'ember', x:(r()-.5)*10, h:4+r()*6, vx:(r()-.5)*6, vh:9+r()*12, age:0, life:1.6+r()*2.4, s:.9+r()*1.2});
        else parts.push({src, k:'smoke', x:(r()-.5)*12*src.big, h:12+r()*8, vx:(r()-.5)*2, vh:6+r()*4, age:0, life:7+r()*5, s:(18+r()*10)*src.big, rot:r()*6.28});
      }
    }
    let windT = 0;
    function fireFrame(dt, t){
      const w = fc.clientWidth, h = fc.clientHeight, dpr = Math.min(devicePixelRatio, 2);
      if (fc.width !== Math.round(w*dpr)) { fc.width = Math.round(w*dpr); fc.height = Math.round(h*dpr); }
      fctx.setTransform(dpr, 0, 0, dpr, 0, 0); fctx.clearRect(0, 0, w, h);
      if (fireAmt <= .01 && !parts.length) return;
      // pixels per metre on screen, from the close-up tile's on-screen size (exaggerated so the effect reads at this scale)
      const tr = hires.getBoundingClientRect(), ppm = Math.max(.32, tr.width / 3720 * 2.4);
      windT += dt; const gust = 1 + .8*Math.sin(windT*.55) * (.6 + .4*Math.sin(windT*.21)), wind = 5.5*gust;
      fireAnchors.forEach(src => {
        const b = src.a.getBoundingClientRect(); src.sx = b.left; src.sy = b.top;
        if (fireAmt > .01 && !reduce) {
          const flare = .75 + .3*Math.sin(t*3.1 + src.big*5) + .2*Math.sin(t*7.7) + .1*Math.sin(t*13.3);
          const acc = (emitAcc.get(src) || 0) + dt * fireAmt;
          emitAcc.set(src, acc % (1/60));
          const steps = Math.floor(acc * 60);
          for (let i = 0; i < steps; i++){ emit(src, 'flame', Math.random() < .9*flare ? 2 : 1); emit(src, 'core', 1); if (Math.random() < .35) emit(src, 'ember', 1); if (Math.random() < .42) emit(src, 'smoke', 1); }
        }
      });
      // ground glow under each fire
      fctx.globalCompositeOperation = 'lighter';
      fireAnchors.forEach(src => { const fl = .55 + .2*Math.sin(t*7.3 + src.big) + .12*Math.sin(t*12.9); const R = 70*ppm*src.big;
        fctx.globalAlpha = fl * fireAmt; fctx.drawImage(SP.glow, src.sx - R, src.sy - R*.55, R*2, R*1.1); });
      // update
      for (let i = parts.length - 1; i >= 0; i--){
        const p = parts[i]; p.age += dt; if (p.age >= p.life) { parts.splice(i, 1); continue; }
        if (p.k === 'smoke') { p.vx += (wind - p.vx) * dt * .35 + Math.sin(t*1.3 + p.rot + p.age*.9) * 1.6 * dt * 6; p.vh *= (1 - dt*.04); }
        else if (p.k === 'ember') { p.vx += (wind*1.2 - p.vx) * dt * .8 + (Math.random()-.5) * 30 * dt; p.vh -= 1.5*dt; }
        else { p.vx += (wind*.25 - p.vx) * dt * 2 + (Math.random()-.5) * 18 * dt; p.vh += 6*dt; }
        p.x += p.vx * dt; p.h += p.vh * dt;
      }
      // draw smoke first (normal blend), then fire (additive)
      fctx.globalCompositeOperation = 'source-over';
      for (const p of parts) if (p.k === 'smoke') {
        const u = p.age / p.life, s = p.s * (1 + u*3.6) * ppm, a = (u < .1 ? u/.1 : 1 - (u-.1)/.9) * .78;
        fctx.globalAlpha = a * Math.max(fireAmt, .001 + (fireAmt>0?0:1)) ; fctx.drawImage(SP.smoke, p.src.sx + p.x*ppm - s/2, p.src.sy - p.h*ppm - s/2, s, s);
      }
      fctx.globalCompositeOperation = 'lighter';
      for (const p of parts) if (p.k !== 'smoke') {
        const u = p.age / p.life; let img = SP.flame, s = p.s * ppm, a = 1;
        if (p.k === 'core') { img = SP.core; s *= (1 - u*.6); a = (1 - u); }
        else if (p.k === 'flame') { img = u < .45 ? SP.flame : SP.red; s *= (1.1 - u*.75); a = u < .15 ? u/.15 : (1 - u); }
        else { img = SP.ember; s = Math.max(2.2, p.s * ppm * 1.6); a = (1 - u) * (.6 + .4*Math.sin(p.age*30)); }
        fctx.globalAlpha = clamp(a, 0, 1) * clamp(fireAmt * 1.4); fctx.drawImage(img, p.src.sx + p.x*ppm - s/2, p.src.sy - p.h*ppm - s/2, s, s);
      }
      fctx.globalAlpha = 1; fctx.globalCompositeOperation = 'source-over';
    }

    /* =================== three.js Earth =================== */
    const canvas = $('#globe');
    const renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    cleanups.push(() => renderer.dispose());
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor(0x020305, 1);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 400);
    const TEX = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/textures/planets/';
    const loader = new THREE.TextureLoader(); loader.setCrossOrigin('anonymous');
    const tex = (f, srgb=true) => { const t = loader.load(TEX + f); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = renderer.capabilities.getMaxAnisotropy(); return t; };
    const sunDir = new THREE.Vector3(-0.85, 0.22, 0.48).normalize();
    const earthMat = new THREE.ShaderMaterial({
      uniforms:{ dayMap:{value:tex('earth_atmos_2048.jpg')}, nightMap:{value:tex('earth_lights_2048.png')}, specMap:{value:tex('earth_specular_2048.jpg', false)}, sunDir:{value:sunDir} },
      vertexShader:`varying vec2 vUv; varying vec3 vN; varying vec3 vP;
        void main(){ vUv=uv; vN=normalize(mat3(modelMatrix)*normal); vec4 wp=modelMatrix*vec4(position,1.); vP=wp.xyz; gl_Position=projectionMatrix*viewMatrix*wp; }`,
      fragmentShader:`uniform sampler2D dayMap,nightMap,specMap; uniform vec3 sunDir; varying vec2 vUv; varying vec3 vN; varying vec3 vP;
        void main(){
          vec3 n=normalize(vN); float d=dot(n,sunDir); float dayAmt=smoothstep(-.12,.28,d);
          vec3 day=texture2D(dayMap,vUv).rgb; vec3 night=texture2D(nightMap,vUv).rgb;
          vec3 V=normalize(cameraPosition-vP); vec3 H=normalize(sunDir+V);
          float spec=pow(max(dot(n,H),0.),90.)*texture2D(specMap,vUv).r*.28*dayAmt;
          vec3 lit=day*(.08+1.05*max(d,0.))+spec*vec3(1.,.95,.85);
          vec3 col=mix(night*vec3(1.,.78,.5)*1.9+day*.015, lit, dayAmt);
          float fr=pow(1.-max(dot(V,n),0.),3.);
          col+=vec3(.25,.5,1.)*fr*.55*smoothstep(-.35,.55,d);
          gl_FragColor=vec4(col,1.);
          #include <colorspace_fragment>
        }`
    });
    const earth = new THREE.Mesh(new THREE.SphereGeometry(1, 160, 160), earthMat);
    const clouds = new THREE.Mesh(new THREE.SphereGeometry(1.008, 128, 128), new THREE.MeshLambertMaterial({map:tex('earth_clouds_1024.png'), transparent:true, opacity:.55, depthWrite:false}));
    const atmo = new THREE.Mesh(new THREE.SphereGeometry(1.055, 96, 96), new THREE.ShaderMaterial({
      uniforms:{sunDir:{value:sunDir}}, side:THREE.BackSide, transparent:true, blending:THREE.AdditiveBlending, depthWrite:false,
      vertexShader:`varying vec3 vN; varying vec3 vW; void main(){ vN=normalize(normalMatrix*normal); vW=normalize(mat3(modelMatrix)*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
      fragmentShader:`uniform vec3 sunDir; varying vec3 vN; varying vec3 vW;
        void main(){ float i=pow(.72-dot(vN,vec3(0.,0.,1.)),3.2); float lit=smoothstep(-.4,.6,dot(vW,sunDir)); gl_FragColor=vec4(vec3(.32,.6,1.)*i*(.25+.95*lit),1.); }`
    }));
    const globe = new THREE.Group(); globe.add(earth, clouds); scene.add(globe, atmo);
    const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.copy(sunDir).multiplyScalar(10); scene.add(sun, new THREE.AmbientLight(0x223344, .25));
    const starMat = new THREE.ShaderMaterial({ uniforms:{t:{value:0}, px:{value:renderer.getPixelRatio()}}, transparent:true, depthWrite:false, blending:THREE.AdditiveBlending,
      vertexShader:`attribute float size; attribute float phase; attribute vec3 tint; uniform float t,px; varying float vA; varying vec3 vT;
        void main(){ vT=tint; vA=.55+.45*sin(t*(.6+phase*1.7)+phase*30.); vec4 mv=modelViewMatrix*vec4(position,1.); gl_PointSize=size*px*(1.+.25*vA); gl_Position=projectionMatrix*mv; }`,
      fragmentShader:`varying float vA; varying vec3 vT; void main(){ vec2 c=gl_PointCoord-.5; float d=length(c); float a=smoothstep(.5,0.,d); a*=a; gl_FragColor=vec4(vT,a*vA); }` });
    {
      const N = 9000, pos = new Float32Array(N*3), size = new Float32Array(N), phase = new Float32Array(N), tint = new Float32Array(N*3);
      for (let i=0;i<N;i++){ const u=Math.random()*2-1, th=Math.random()*Math.PI*2, r=120+Math.random()*120, s=Math.sqrt(1-u*u);
        pos.set([r*s*Math.cos(th), r*u, r*s*Math.sin(th)], i*3); const big = Math.random()<.04; size[i] = big ? 2.4+Math.random()*2.2 : .7+Math.random()*1.4; phase[i]=Math.random();
        const w=Math.random(); tint.set(w<.15?[.75,.85,1]:w<.25?[1,.88,.72]:[1,1,1], i*3); }
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(pos,3)); g.setAttribute('size', new THREE.BufferAttribute(size,1));
      g.setAttribute('phase', new THREE.BufferAttribute(phase,1)); g.setAttribute('tint', new THREE.BufferAttribute(tint,3));
      scene.add(new THREE.Points(g, starMat));
    }
    function faceAngles(lon, lat){ const th = (lon+180)/360*Math.PI*2, ph = lat*Math.PI/180; const x = -Math.cos(th)*Math.cos(ph), z = Math.sin(th)*Math.cos(ph); return {y:-Math.atan2(x, z), x:ph}; }
    const face = faceAngles(35.55, 33.25);
    const wrapPi = a => Math.atan2(Math.sin(a), Math.cos(a));
    function resize(){ const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w/h; camera.updateProjectionMatrix(); }
    window.addEventListener('resize', resize); cleanups.push(() => window.removeEventListener('resize', resize)); resize();

    /* =================== main loop =================== */
    let p = 0, ps = 0, spin = face.y - 1.9;
    const clock = new THREE.Clock();
    function frame(){
      const dt = Math.min(.05, clock.getDelta()), t = clock.elapsedTime;
      ps += (p - ps) * (reduce ? 1 : Math.min(1, dt*4.5));
      // globe (hidden once the bird view has taken over)
      if (ps < .45) {
        starMat.uniforms.t.value = t;
        const dive = ease(range(ps, .07, .30));
        if (!reduce) spin += dt * .06 * (1 - dive);
        globe.rotation.set(face.x * (.35 + .65*dive), spin + wrapPi(face.y - spin) * dive, 0);
        clouds.rotation.y += dt * .008;
        const mob = innerWidth <= 600, z0 = mob ? 6.2 : (innerHeight < 760 ? 4.5 : 4.15);
        // globe centre at ~72% of the width on any desktop aspect: x_ndc = -c / (z0 * tan(fov/2) * aspect)
        const wide = innerWidth > 900 ? -0.44 * Math.tan(THREE.MathUtils.degToRad(camera.fov/2)) * camera.aspect * z0 : 0;
        camera.position.set(wide * (1-dive), (mob ? -0.55 : 0) * (1-dive), z0 - (z0 - 1.18) * dive);
        camera.lookAt(wide * (1-dive), (mob ? -0.2 : 0) * (1-dive), 0);
        canvas.style.opacity = 1 - ease(range(ps, .25, .33));
        canvas.style.filter = `blur(${(range(ps, .18, .31) * 7).toFixed(2)}px)`;
        renderer.render(scene, camera);
      } else canvas.style.opacity = 0;
      // screen-space markers follow their ground anchors
      const birdOn = ps > .24 && ps < .99;
      groupOpacity.reg = range(ps, .36, .40) * (1 - range(ps, .50, .54));
      groupOpacity.zoom = range(ps, .60, .64) * (1 - range(ps, .93, .97));
      fireAmt = range(ps, .56, .62) * (1 - range(ps, .93, .98));
      for (const m of markers) {
        const o = groupOpacity[m.group];
        if (!birdOn || o <= .001) { if (m.el.style.opacity !== '0') m.el.style.opacity = 0; continue; }
        const r = m.a.getBoundingClientRect();
        m.el.style.transform = `translate3d(${r.left.toFixed(1)}px, ${r.top.toFixed(1)}px, 0)`;
        m.el.style.opacity = o;
      }
      fireFrame(dt, t);
      if (alive) rafId = requestAnimationFrame(frame);
    }
    rafId = requestAnimationFrame(frame);

    /* =================== GSAP: smooth scroll + story =================== */
    if (!reduce) {
      const lenis = window.__lenis = new Lenis({lerp:.085, smoothWheel:true});
      lenis.on('scroll', ScrollTrigger.update);
      const tick = time => lenis.raf(time * 1000); gsap.ticker.add(tick); gsap.ticker.lagSmoothing(0);
      cleanups.push(() => { gsap.ticker.remove(tick); lenis.destroy(); delete window.__lenis; });
      root.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', e => { const el = root.querySelector(a.getAttribute('href')); if (el){ e.preventDefault(); lenis.scrollTo(el, {offset:-20, duration:1.8}); } }));
    }
    ScrollTrigger.create({ trigger:'#hero', start:'top top', end:'bottom bottom', onUpdate:s => { p = s.progress; } });
    ScrollTrigger.create({ start:80, onToggle:s => $('#nav').classList.toggle('top', !s.isActive) });

    gsap.from('.hero-copy h1 .line>span', {yPercent:110, duration:1.3, ease:'expo.out', stagger:.12, delay:.25});
    gsap.from(['.hero-copy .kicker','.hero-copy p','.hero-cta','#hint'], {opacity:0, y:24, duration:1.1, ease:'power3.out', stagger:.12, delay:.7});

    const tl = gsap.timeline({ defaults:{ease:'none'}, scrollTrigger:{ trigger:'#hero', start:'top top', end:'bottom bottom', scrub:reduce ? true : 1.1 } });
    tl.set({}, {}, 1);
    // 1) headline leaves, the globe dives
    tl.to('#copy', {opacity:0, y:-60, filter:'blur(6px)', duration:.07}, .04)
      .to('#tfade', {opacity:0, duration:.07}, .05)
      .to('#hint', {opacity:0, duration:.03}, .02)
      .fromTo('#cap1', {opacity:0, y:20}, {opacity:1, y:0, duration:.04}, .12)
      .to('#cap1', {opacity:0, y:-20, duration:.04}, .24);
    // 2) regional bird view: straight down, then tilt — four ranked incidents
    tl.fromTo('#bird', {opacity:0, filter:'blur(10px)'}, {opacity:1, filter:'blur(0px)', duration:.08}, .25)
      .fromTo('#shade', {opacity:0}, {opacity:1, duration:.08}, .27)
      .fromTo('#plane', {scale:.85, rotateX:0, rotateZ:-10}, {scale:3.2, rotateX:38, rotateZ:-4, duration:.25, ease:'power2.inOut'}, .27)
      .fromTo('.regdot', {opacity:0}, {opacity:1, duration:.03}, .36)
      .to('.regdot', {opacity:0, duration:.03}, .50)
      .fromTo('#cap2', {opacity:0, y:20}, {opacity:1, y:0, duration:.04}, .37)
      .to('#cap2', {opacity:0, y:-20, duration:.04}, .49);
    // 3) close-up of Khiam: sharp tile fades in, camera drops and tilts; damage, fire, routes, shelters appear
    tl.to('#plane', {scale:15, rotateX:56, rotateZ:-8, duration:.16, ease:'power2.inOut'}, .50)
      .fromTo('#hires', {opacity:0}, {opacity:1, duration:.05}, .52)
      .fromTo('.z-ring', {opacity:0}, {opacity:1, duration:.03}, .58)
      .fromTo('.z-dmg', {opacity:0}, {opacity:1, duration:.04, stagger:.004}, .58)
      .fromTo('#g-routes', {opacity:0}, {opacity:1, duration:.04}, .61)
      .fromTo('#capZ', {opacity:0, y:20}, {opacity:1, y:0, duration:.04}, .62)
      .to('#capZ', {opacity:0, y:-20, duration:.04}, .71)
      // a slow orbit while the cards arrive
      .to('#plane', {scale:16.5, rotateZ:6, duration:.27, ease:'sine.inOut'}, .66);
    // 4) plain-language dashboard cards float in (no clicks), then everything clears
    const cardIds = ['#fc-rank','#fc-inc','#fc-fire','#fc-power','#fc-route','#fc-shelter','#fc-pass'];
    tl.fromTo('#cap3', {opacity:0, y:16}, {opacity:1, y:0, duration:.04}, .74)
      .fromTo(cardIds, {opacity:0, y:40, scale:.94, filter:'blur(8px)'}, {opacity:1, y:0, scale:1, filter:'blur(0px)', duration:.05, stagger:.018, ease:'power3.out'}, .73)
      .to(cardIds, {opacity:0, y:-24, duration:.04, stagger:.006}, .93)
      .to(['#cap3','#bird','#shade'], {opacity:0, duration:.05}, .94);
    if (!reduce) cardIds.forEach((c, i) => gsap.to(c, {yPercent:'+=3', duration:2.8 + i*.3, ease:'sine.inOut', yoyo:true, repeat:-1}));

    /* =================== sections =================== */
    Array.from(root.querySelectorAll('.reveal')).forEach(el => gsap.to(el, {opacity:1, y:0, duration:1.1, ease:'power3.out', scrollTrigger:{trigger:el, start:'top 88%'}}));
    if ($('#pulse')) gsap.to('#pulse', {left:'86%', duration:3.2, ease:'power1.inOut', repeat:-1, scrollTrigger:{trigger:'#how', start:'top 70%', toggleActions:'play pause resume pause'}});
    root.querySelectorAll('.shot[data-bbox]').forEach(s => { s.style.backgroundImage = `url("${esri(s.dataset.bbox, 800, 600)}")`; });
  }, root)
  return () => {
    alive = false
    cancelAnimationFrame(rafId)
    ctx.revert()
    ScrollTrigger.getAll().forEach(t => t.kill())
    cleanups.forEach(f => { try { f() } catch { /* already gone */ } })
  }
}
