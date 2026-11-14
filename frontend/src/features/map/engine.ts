// CesiumJS map engine: globe, terrain, OSM buildings, overlays, fire/damage effects, camera flights.
// React owns the UI state and calls into this class; the class owns every Cesium object.
// Ported from docs/design/civisar-3d-map-mockup.html (the UI source of truth).
import * as C from 'cesium'
import type { BaseMap, DamageClass, Fire, Incident, Layers, LonLat, MapData, Path, ViewMode } from '../../types/map'
import { dist, fmtM, passIndex, pathStats, rawPaths, runs, visibleAt } from './analysis'

export const DMG_COLOR: Record<DamageClass, string> = { destroyed: '#ff7a93', severe: '#f5904f', moderate: '#f2b84b', possible: '#eadf73' }
export const DMG_LABEL: Record<DamageClass, string> = {
  destroyed: 'Destroyed (candidate)', severe: 'Severe (candidate)', moderate: 'Moderate (candidate)', possible: 'Possible damage (candidate)',
}
const COL = { corroborated: '#45c79c', fire: '#ff8a4d', radar: '#c39be8', power: '#9d93e6', open: '#f1f4f3', blocked: '#ff5a5f' }
const css = (c: string) => C.Color.fromCssColorString(c)
const reduceMotion = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

export type BuildingInfo = {
  name: string; id: string; use: string; material: string | null; height: string; floors: string
  facility: boolean; residents: string; cell: MapData['damage_cells'][number] | null
}
export type EngineEvents = {
  phase: (p: number) => void
  pickIncident: (id: string) => void
  pickShelter: (id: string) => void
  pickBuilding: (b: BuildingInfo) => void
  banner: (msg: string) => void
  roads: () => void
  orbit: (on: boolean) => void
}
type Tagged = C.Entity & { _layer?: string; _pass?: number; _incident?: string; _shelter?: string; _forIncident?: string; _path?: boolean }
type FxSystem = C.ParticleSystem & { _layer: keyof Layers; _pass: number }
type Particle = C.Particle & { _age?: number }

/* ---------- canvas images ---------- */
function canvas(w: number, h = w) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')!] as const }
function radial(stops: [number, string][], size = 128) {
  const [c, g] = canvas(size); const gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  stops.forEach(([o, cl]) => gr.addColorStop(o, cl)); g.fillStyle = gr; g.fillRect(0, 0, size, size); return c
}
function ringImg() {
  const [c, g] = canvas(256); const gr = g.createRadialGradient(128, 128, 90, 128, 128, 128)
  gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.75, 'rgba(255,255,255,.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)')
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256); return c
}
function pinImg(rank: number, color: string) {
  const [c, g] = canvas(96, 112)
  g.fillStyle = 'rgba(0,0,0,.35)'; g.beginPath(); g.ellipse(48, 104, 14, 5, 0, 0, 7); g.fill()
  g.beginPath(); g.moveTo(48, 102); g.lineTo(36, 70); g.lineTo(60, 70); g.closePath(); g.fillStyle = color; g.fill()
  g.beginPath(); g.arc(48, 44, 34, 0, 7); g.fillStyle = color; g.fill()
  g.beginPath(); g.arc(48, 44, 27, 0, 7); g.fillStyle = '#0e1215'; g.fill()
  g.fillStyle = '#f1f4f3'; g.font = "600 28px 'JetBrains Mono',monospace"; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(rank), 48, 46)
  return c
}
function badgeImg(letter: string, shelter = false) {
  const [c, g] = canvas(56)
  if (shelter) {
    g.setLineDash([5, 4]); g.strokeStyle = '#f1f4f3'; g.lineWidth = 3; g.beginPath(); g.roundRect(5, 5, 46, 46, 14); g.stroke()
    g.setLineDash([]); g.fillStyle = 'rgba(14,18,21,.92)'; g.beginPath(); g.roundRect(9, 9, 38, 38, 10); g.fill()
    g.strokeStyle = '#f1f4f3'; g.lineWidth = 2.6; g.lineJoin = 'round'; g.beginPath()
    g.moveTo(18, 29); g.lineTo(28, 20); g.lineTo(38, 29); g.moveTo(21, 27); g.lineTo(21, 38); g.lineTo(35, 38); g.lineTo(35, 27); g.stroke(); return c
  }
  g.fillStyle = '#f1f4f3'; g.beginPath(); g.roundRect(8, 8, 40, 40, 11); g.fill()
  g.fillStyle = '#0e1215'; g.font = '700 20px Inter,sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(letter, 28, 29); return c
}
let IMG: Record<string, HTMLCanvasElement> | null = null
function fxImages() {
  if (IMG) return IMG
  IMG = {
    core: radial([[0, 'rgba(255,255,240,1)'], [0.3, 'rgba(255,236,170,.95)'], [0.7, 'rgba(255,170,60,.4)'], [1, 'rgba(255,120,30,0)']], 64),
    flame: radial([[0, 'rgba(255,230,160,1)'], [0.25, 'rgba(255,170,60,.9)'], [0.6, 'rgba(240,80,20,.5)'], [1, 'rgba(200,40,10,0)']]),
    ember: radial([[0, 'rgba(255,245,210,1)'], [0.35, 'rgba(255,170,70,.95)'], [1, 'rgba(255,90,20,0)']], 32),
    smoke: radial([[0, 'rgba(58,54,50,.85)'], [0.45, 'rgba(52,50,48,.5)'], [1, 'rgba(45,45,45,0)']]),
    dust: radial([[0, 'rgba(170,150,120,.6)'], [0.5, 'rgba(150,135,110,.3)'], [1, 'rgba(140,125,100,0)']]),
    glow: radial([[0, 'rgba(255,160,70,.95)'], [0.3, 'rgba(255,110,40,.5)'], [1, 'rgba(255,80,20,0)']], 256),
    ring: ringImg(),
  }
  return IMG
}

/* ---------- geometry ---------- */
function square(lon: number, lat: number, m: number) {
  const dLat = m / 2 / 111320, dLon = m / 2 / (111320 * Math.cos((lat * Math.PI) / 180))
  return [lon - dLon, lat - dLat, lon + dLon, lat - dLat, lon + dLon, lat + dLat, lon - dLon, lat + dLat]
}
const ring = (a: number[]) => [...a, a[0], a[1]]
function circle(lon: number, lat: number, r: number, n = 72) {
  const out: number[] = []
  for (let i = 0; i <= n; i++) { const a = (i / n) * 2 * Math.PI; out.push(lon + (r * Math.cos(a)) / (111320 * Math.cos((lat * Math.PI) / 180)), lat + (r * Math.sin(a)) / 111320) }
  return C.Cartesian3.fromDegreesArray(out)
}
const FONT = (w: number) => `${w} 13px Inter, sans-serif`
function label(text: string, o: Partial<C.LabelGraphics.ConstructorOptions> = {}): C.LabelGraphics.ConstructorOptions {
  return {
    text, font: FONT(600), fillColor: css('#f1f4f3'), showBackground: true, backgroundColor: css('rgba(10,13,15,0.86)'),
    backgroundPadding: new C.Cartesian2(9, 6), horizontalOrigin: C.HorizontalOrigin.LEFT, verticalOrigin: C.VerticalOrigin.CENTER,
    pixelOffset: new C.Cartesian2(28, -26), disableDepthTestDistance: Number.POSITIVE_INFINITY, heightReference: C.HeightReference.CLAMP_TO_GROUND, ...o,
  }
}

/* ---------- OSM building colours (material tag first, then use, then neutral stone) ---------- */
const MAT = [['stone', '#c9b99a'], ['brick', '#b5684c'], ['concrete', '#b9b6ae'], ['plaster', '#e4dac4'], ['cement_block', '#b3afa6'],
  ['wood', '#a07f5c'], ['metal', '#a4a8aa'], ['glass', '#9fb0b6'], ['limestone', '#d8ccb0'], ['sandstone', '#cdb38a']]
const USE = [['house', '#dccfb4'], ['residential', '#d8ccb2'], ['apartments', '#d3c8b1'], ['commercial', '#c4bfb5'], ['retail', '#c6bfb2'],
  ['industrial', '#a9aaa6'], ['warehouse', '#aeaca5'], ['mosque', '#e6dfcd'], ['church', '#ddd3bd'], ['school', '#cfc3a8'], ['hospital', '#d9d6cf']]
function buildingStyle(alpha: number) {
  const conds: [string, string][] = []
  MAT.forEach(([m, c]) => conds.push([`\${feature['building:material']} === '${m}'`, `color('${c}', ${alpha})`]))
  conds.push([`\${feature['roof:material']} === 'roof_tiles' || \${feature['roof:material']} === 'tile'`, `color('#b8714f', ${alpha})`])
  USE.forEach(([u, c]) => conds.push([`\${feature['building']} === '${u}'`, `color('${c}', ${alpha})`]))
  conds.push(['true', `color('#cfc6b4', ${alpha})`])
  return new C.Cesium3DTileStyle({ color: { conditions: conds }, show: alpha > 0.02 ? 'true' : 'false' })
}

const ESRI = (p: string) => `https://server.arcgisonline.com/ArcGIS/rest/services/${p}/MapServer/tile/{z}/{y}/{x}`
const BIRD = { lon: 35.47, lat: 32.8, h: 44000, heading: 4, pitch: -42 }
const REGION = () => C.Rectangle.fromDegrees(35.15, 33.02, 35.8, 33.45)
const cinematic = (t: number) => { const u = 1 - Math.pow(1 - t, 1.7); return u * u * (3 - 2 * u) }

export class MapEngine {
  v3: C.Viewer | null = null
  v2: C.Viewer | null = null
  paths: Path[]
  roadsLoaded = false
  private tileset: (C.Cesium3DTileset & { _alpha?: number }) | null = null
  private edge: C.PostProcessStage | null = null
  private fx: FxSystem[] = []
  private overlays = new Map<C.Viewer, C.ImageryLayer[]>()
  private heightsReady: Promise<void> = Promise.resolve()
  private flying = false
  private phase = 0
  private orbitT: { target: C.Cartesian3; range: number; pitch: number; heading: number; speed: number; left: number; last: number; arrival: boolean } | null = null
  private t0 = performance.now()
  private destroyed = false
  layers: Layers
  passIdx: number
  selected: string | null = null
  mode: ViewMode = '3d'
  base: BaseMap = 'sat'

  constructor(private data: MapData, private token: string | null, private ev: EngineEvents, layers: Layers, passIdx: number) {
    this.layers = { ...layers }
    this.passIdx = passIdx
    this.paths = rawPaths(data)
    if (token) C.Ion.defaultAccessToken = token
  }

  private now = () => (performance.now() - this.t0) / 1000

  /* ---------- viewers ---------- */
  private makeViewer(el: HTMLElement, mode: C.SceneMode, creditEl?: HTMLElement) {
    const is3D = mode === C.SceneMode.SCENE3D
    const v = new C.Viewer(el, {
      baseLayer: false, sceneMode: mode, animation: false, timeline: false, baseLayerPicker: false, geocoder: false, homeButton: false,
      sceneModePicker: false, navigationHelpButton: false, fullscreenButton: false, infoBox: false, selectionIndicator: false,
      creditContainer: creditEl ?? document.createElement('div'), msaaSamples: 4,
      ...(this.token && is3D ? { terrain: C.Terrain.fromWorldTerrain({ requestVertexNormals: true, requestWaterMask: true }) } : {}),
    })
    this.setupImagery(v)
    const sc = v.scene
    // Google-Earth-style space: black with the star field, no sun/moon sprites; the atmosphere rim stays
    sc.backgroundColor = C.Color.BLACK
    if (sc.skyBox) sc.skyBox.show = true
    if (sc.sun) sc.sun.show = false
    if (sc.moon) sc.moon.show = false
    sc.globe.baseColor = css('#0f2433') // dark ocean blue until imagery tiles arrive; sc.globe.depthTestAgainstTerrain = true
    sc.globe.enableLighting = !!this.token
    sc.fog.enabled = true; sc.fog.density = 1.4e-4; sc.fog.minimumBrightness = 0.08
    if (sc.skyAtmosphere) { sc.skyAtmosphere.saturationShift = -0.3; sc.skyAtmosphere.brightnessShift = -0.15 }
    v.clock.shouldAnimate = true
    v.clock.currentTime = C.JulianDate.fromIso8601('2026-11-14T11:00:00Z')
    sc.light = new C.SunLight({ intensity: 2.2 })
    if (this.token && is3D) { v.shadows = true; v.shadowMap.softShadows = true; v.shadowMap.darkness = 0.45; v.shadowMap.size = 2048 }
    sc.postProcessStages.fxaa.enabled = true
    return v
  }
  private setupImagery(v: C.Viewer) {
    const L = v.imageryLayers; L.removeAll(true)
    const base = L.addImageryProvider(this.base === 'streets'
      ? new C.UrlTemplateImageryProvider({ url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', maximumLevel: 19, credit: '© OpenStreetMap contributors' })
      : new C.UrlTemplateImageryProvider({ url: ESRI('World_Imagery'), maximumLevel: 19, credit: 'Esri, Maxar, Earthstar Geographics' }))
    if (this.base === 'sat') { base.saturation = 0.85; base.brightness = 0.95; base.gamma = 1.05 }
    else { base.brightness = 0.55; base.contrast = 1.15; base.saturation = 0.25; base.gamma = 1.1 }
    const ov = this.base === 'sat'
      ? ['Reference/World_Transportation', 'Reference/World_Boundaries_and_Places'].map(p => { const l = L.addImageryProvider(new C.UrlTemplateImageryProvider({ url: ESRI(p), maximumLevel: 19, credit: 'Esri' })); l.alpha = 0.9; return l })
      : []
    this.overlays.set(v, ov)
  }

  /** Mounts the 3D viewer, starts the globe → bird view flight and loads roads, buildings and effects. */
  mount3d(el: HTMLElement, creditEl: HTMLElement) {
    const v = this.v3 = this.makeViewer(el, C.SceneMode.SCENE3D, creditEl)
    if (this.token) this.heightsReady = new Promise<void>(res => {
      const go = () => this.sampleHeights(v).then(res, () => res())
      if (!(v.scene.terrainProvider instanceof C.EllipsoidTerrainProvider)) go()
      else { const off = v.scene.globe.terrainProviderChanged.addEventListener(() => { off(); go() }) }
    })
    this.buildEntities(v, true)
    if (this.token) this.loadBuildings(v)
    this.pickHandler(v)
    v.scene.preRender.addEventListener(() => this.tick(v))
    this.heightsReady.then(() => { if (!this.destroyed) { this.build3DExtras(v); this.refresh() } })
    // START: whole Earth on black, turned slightly west of Lebanon; the flight rotates it into place
    v.camera.setView({ destination: C.Cartesian3.fromDegrees(8, 22, 2.6e7) })
    this.refresh()
    // hold the full-Earth view until its imagery has loaded (max 6 s), pause, then fly in
    if (reduceMotion()) this.flyBird(0)
    else {
      const t0 = performance.now()
      const off = v.scene.postRender.addEventListener(() => {
        if (v.scene.globe.tilesLoaded || performance.now() - t0 > 6000) { off(); setTimeout(() => { if (!this.destroyed) this.flyBird(7) }, 1600) }
      })
    }
    this.loadRoads()
  }
  mount2d(el: HTMLElement) {
    if (this.v2) return
    const v = this.v2 = this.makeViewer(el, C.SceneMode.SCENE2D)
    this.buildEntities(v, false); this.pickHandler(v); this.refresh()
    const inc = this.data.incidents.find(i => i.id === this.selected)
    v.camera.setView({ destination: inc ? C.Cartesian3.fromDegrees(inc.lon, inc.lat, 2600) : REGION() })
  }
  destroy() {
    this.destroyed = true
    ;[this.v3, this.v2].forEach(v => v && !v.isDestroyed() && v.destroy())
    this.v3 = this.v2 = null
  }

  /* ---------- entities shared by 2D and 3D ---------- */
  private buildEntities(v: C.Viewer, is3D: boolean) {
    const D = this.data, E = v.entities, pi = (id: string) => passIndex(D, id)
    const add = (layer: string, pass: number, e: C.Entity.ConstructorOptions, extra: Partial<Tagged> = {}) => {
      const en = E.add(e) as Tagged; en._layer = layer; en._pass = pass; Object.assign(en, extra); return en
    }
    const near = new C.DistanceDisplayCondition(0, 7000)
    D.incidents.forEach(inc => add('incident', pi(inc.first_pass), {
      position: C.Cartesian3.fromDegrees(inc.lon, inc.lat),
      billboard: { image: pinImg(inc.rank, DMG_COLOR[inc.damage_class]), scale: 0.5, verticalOrigin: C.VerticalOrigin.BOTTOM, heightReference: C.HeightReference.CLAMP_TO_GROUND, disableDepthTestDistance: Number.POSITIVE_INFINITY },
      label: label(inc.name, { pixelOffset: new C.Cartesian2(22, -34), distanceDisplayCondition: new C.DistanceDisplayCondition(1800, 4e5) }),
    }, { _incident: inc.id }))
    D.damage_cells.forEach(d => {
      const c = css(DMG_COLOR[d.damage_class]), p = pi(d.pass_id), sq = square(d.lon, d.lat, d.size_m)
      add('damage', p, { polygon: { hierarchy: new C.PolygonHierarchy(C.Cartesian3.fromDegreesArray(sq)),
        material: new C.StripeMaterialProperty({ evenColor: c.withAlpha(0.7), oddColor: c.withAlpha(0.06), repeat: 7, orientation: C.StripeOrientation.VERTICAL }),
        stRotation: C.Math.toRadians(45), classificationType: C.ClassificationType.TERRAIN } })
      add('damage', p, { polyline: { positions: C.Cartesian3.fromDegreesArray(ring(sq)), clampToGround: true, width: 2, material: c } })
      if (d.second_sensor) add('second', p, { polyline: { positions: circle(d.lon, d.lat, d.size_m * 0.95), clampToGround: true, width: 2.5,
        material: new C.PolylineDashMaterialProperty({ color: css(COL.corroborated), dashLength: 14 }) } })
    })
    D.change_cells.forEach(c => add('change', pi(c.pass_id), { polyline: { positions: C.Cartesian3.fromDegreesArray(ring(square(c.lon, c.lat, c.size_m))), clampToGround: true, width: 2, material: css(COL.radar).withAlpha(0.9) } }))
    D.fires.forEach(f => {
      const p = pi(f.pass_id)
      add('fires', p, { polyline: { positions: circle(f.lon, f.lat, f.uncertainty_m), clampToGround: true, width: 2, material: new C.PolylineDashMaterialProperty({ color: css(COL.fire).withAlpha(0.9), dashLength: 18 }) } })
      add('fires', p, { position: C.Cartesian3.fromDegrees(f.lon, f.lat),
        point: is3D ? undefined : { pixelSize: 11, color: css(COL.fire), outlineColor: C.Color.BLACK, outlineWidth: 2, heightReference: C.HeightReference.CLAMP_TO_GROUND },
        label: label(is3D ? 'Fire · illustrative effect' : 'Fire · 375 m ring', { font: "500 12px 'JetBrains Mono', monospace", pixelOffset: new C.Cartesian2(16, -44), fillColor: css('#ffc7a8'), distanceDisplayCondition: new C.DistanceDisplayCondition(0, is3D ? 3500 : 12000) }) })
    })
    D.nightlights.forEach(n => {
      const p = pi(n.pass_id), dark = n.state === 'dark', sq = square(n.lon, n.lat, n.size_m)
      add('night', p, { polygon: { hierarchy: new C.PolygonHierarchy(C.Cartesian3.fromDegreesArray(sq)),
        material: dark ? new C.StripeMaterialProperty({ evenColor: css(COL.power).withAlpha(0.38), oddColor: css('#04050a').withAlpha(0.42), repeat: 16, orientation: C.StripeOrientation.HORIZONTAL }) : css('#f3e3a1').withAlpha(0.12),
        classificationType: C.ClassificationType.TERRAIN } })
      if (dark) add('night', p, { polyline: { positions: C.Cartesian3.fromDegreesArray(ring(sq)), clampToGround: true, width: 1.5, material: new C.PolylineDashMaterialProperty({ color: css(COL.power), dashLength: 10 }) } })
    })
    D.population.forEach(p => add('pop', 0, {
      polygon: { hierarchy: new C.PolygonHierarchy(C.Cartesian3.fromDegreesArray(square(p.lon, p.lat, p.size_m))), material: css('#cfd8d5').withAlpha(0.06 + (p.people.high / 2600) * 0.2), classificationType: C.ClassificationType.TERRAIN },
      position: C.Cartesian3.fromDegrees(p.lon, p.lat),
      label: label(`${p.people.low.toLocaleString('en-US')}–${p.people.high.toLocaleString('en-US')} people`, { font: "500 12px 'JetBrains Mono', monospace", horizontalOrigin: C.HorizontalOrigin.CENTER, pixelOffset: C.Cartesian2.ZERO, distanceDisplayCondition: new C.DistanceDisplayCondition(0, 6000) }),
    }))
    const L: Record<string, string> = { school: 'S', hospital: 'H', clinic: '+', water: 'W', fuel: 'F' }
    D.facilities.forEach(f => add('facilities', 0, { position: C.Cartesian3.fromDegrees(f.lon, f.lat),
      billboard: { image: badgeImg(L[f.kind] || '•'), scale: 0.5, heightReference: C.HeightReference.CLAMP_TO_GROUND, disableDepthTestDistance: Number.POSITIVE_INFINITY },
      label: label(f.name, { font: FONT(500), pixelOffset: new C.Cartesian2(18, 0), distanceDisplayCondition: near }) }))
    D.shelters.forEach(s => add('shelters', 0, { position: C.Cartesian3.fromDegrees(s.lon, s.lat),
      billboard: { image: badgeImg('', true), scale: 0.62, heightReference: C.HeightReference.CLAMP_TO_GROUND, disableDepthTestDistance: Number.POSITIVE_INFINITY },
      label: label(`${s.name} · candidate shelter, not verified`, { font: FONT(500), pixelOffset: new C.Cartesian2(20, 0), distanceDisplayCondition: near }) }, { _shelter: s.id }))
    this.drawPaths(v)
  }

  /* ---------- routes on real roads (free OSRM demo server) ---------- */
  private async osrm(coords: [number, number][]) {
    const a = coords[0], b = coords[coords.length - 1]
    const url = `https://router.project-osrm.org/route/v1/driving/${a[0].toFixed(5)},${a[1].toFixed(5)};${b[0].toFixed(5)},${b[1].toFixed(5)}?overview=full&geometries=geojson`
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 8000)
    try {
      const j = await (await fetch(url, { signal: ctl.signal })).json()
      return j.code === 'Ok' && j.routes[0].geometry.coordinates.length > 1 ? (j.routes[0].geometry.coordinates as [number, number][]) : null
    } catch { return null } finally { clearTimeout(t) }
  }
  private async loadRoads() {
    let ok = 0
    for (const p of this.paths) { // one at a time: polite to the free demo server
      if (this.destroyed) return
      const g = await this.osrm(p.coords)
      if (g) { p.coords = g; p.source = 'osm'; ok++ }
    }
    this.roadsLoaded = true
    ;[this.v3, this.v2].forEach(v => v && this.drawPaths(v)); this.refresh(); this.ev.roads()
    if (!ok) this.ev.banner('Road routing could not be reached. Showing sample route lines instead.')
  }
  private drawPaths(v: C.Viewer) {
    (v.entities.values as Tagged[]).filter(e => e._path).forEach(e => v.entities.remove(e))
    const near = new C.DistanceDisplayCondition(0, 7000)
    const add = (p: Path, e: C.Entity.ConstructorOptions) => {
      const en = v.entities.add(e) as Tagged; en._path = true; en._layer = p.kind === 'shelter' ? 'shelters' : 'routes'; en._pass = 0
      if (p.kind === 'shelter') en._forIncident = p.incident_id
    }
    const red = () => new C.PolylineDashMaterialProperty({ color: css(COL.blocked), gapColor: css('#3a0b0d').withAlpha(0.85), dashLength: 18 })
    this.paths.forEach(p => {
      const st = pathStats(this.data, p, this.passIdx)
      const segs = st.blocked ? [{ f: true, pts: st.pts }] : runs(st.pts, st.near)
      segs.forEach(sg => {
        const pos = C.Cartesian3.fromDegreesArray(sg.pts.flatMap(q => [q.lon, q.lat]))
        if (sg.f) { add(p, { polyline: { positions: pos, clampToGround: true, width: 7, material: red() } }); return }
        add(p, { polyline: { positions: pos, clampToGround: true, width: p.kind === 'shelter' ? 9 : 12, material: css('#0a0d0f').withAlpha(0.55) } })
        add(p, { polyline: { positions: pos, clampToGround: true, width: p.kind === 'shelter' ? 4 : 6,
          material: p.kind === 'shelter' ? new C.PolylineDashMaterialProperty({ color: css(COL.open), gapColor: css('#0a0d0f').withAlpha(0.6), dashLength: 14 }) : css(COL.open) } })
      })
      const m = st.pts[Math.floor(st.pts.length / 2)]
      add(p, { position: C.Cartesian3.fromDegrees(m.lon, m.lat), label: label(st.blocked ? `${p.label} · possibly blocked (candidate)` : `${p.label} · ${fmtM(st.len)} · not verified`,
        { fillColor: st.blocked ? css('#ff9a9d') : css(COL.open), pixelOffset: new C.Cartesian2(14, 18), distanceDisplayCondition: near }) })
      if (!st.blocked) runs(st.pts, st.near).filter(sg => sg.f).forEach(sg => {
        const q = sg.pts[Math.floor(sg.pts.length / 2)]
        add(p, { position: C.Cartesian3.fromDegrees(q.lon, q.lat), label: label('possibly blocked (candidate)', { font: '600 12px Inter, sans-serif', fillColor: css('#ff9a9d'), pixelOffset: new C.Cartesian2(12, -16), distanceDisplayCondition: new C.DistanceDisplayCondition(0, 4000) }) })
      })
    })
  }

  /* ---------- 3D-only: heights, buildings, effects ---------- */
  private async sampleHeights(v: C.Viewer) {
    const pts: LonLat[] = [...this.data.incidents, ...this.data.damage_cells, ...this.data.fires]
    const out = await C.sampleTerrainMostDetailed(v.scene.terrainProvider, pts.map(p => C.Cartographic.fromDegrees(p.lon, p.lat)))
    out.forEach((c, i) => { pts[i].h = c.height || 0 })
  }
  private async loadBuildings(v: C.Viewer) {
    try {
      const ts: C.Cesium3DTileset & { _alpha?: number } = await C.createOsmBuildingsAsync({ style: buildingStyle(0) })
      if (this.destroyed) return
      this.tileset = ts
      ts.maximumScreenSpaceError = 24; ts._alpha = 0
      v.scene.primitives.add(ts)
      if (C.PostProcessStageLibrary.isSilhouetteSupported(v.scene)) {
        const edge = C.PostProcessStageLibrary.createEdgeDetectionStage()
        edge.uniforms.color = css('#ffffff'); edge.uniforms.length = 0.01; edge.selected = []
        v.scene.postProcessStages.add(C.PostProcessStageLibrary.createSilhouetteStage([edge])); this.edge = edge
      }
    } catch (e) { console.warn('OSM buildings failed', e); this.ev.banner('3D buildings could not load. Terrain and imagery still shown.') }
  }
  private addFx(v: C.Viewer, sys: C.ParticleSystem, layer: keyof Layers, pass: number) {
    const s = sys as FxSystem; s._layer = layer; s._pass = pass; v.scene.primitives.add(s); this.fx.push(s); return s
  }
  private frameAt(lon: number, lat: number, h: number) { return C.Transforms.eastNorthUpToFixedFrame(C.Cartesian3.fromDegrees(lon, lat, h)) }
  private build3DExtras(v: C.Viewer) {
    const im = fxImages(), now = this.now
    this.data.damage_cells.forEach((d, idx) => {
      const c = css(DMG_COLOR[d.damage_class]), h = d.h || 0, p = passIndex(this.data, d.pass_id)
      const tall = d.damage_class === 'destroyed' || d.damage_class === 'severe' ? 24 : 16
      const tag = (e: C.Entity) => { const t = e as Tagged; t._layer = 'damage'; t._pass = p }
      // hatched candidate volume around the building footprint (overlay; building colour untouched)
      tag(v.entities.add({ polygon: { hierarchy: new C.PolygonHierarchy(C.Cartesian3.fromDegreesArray(square(d.lon, d.lat, d.size_m))), height: h - 2, extrudedHeight: h + tall,
        material: new C.StripeMaterialProperty({ evenColor: c.withAlpha(0.38), oddColor: c.withAlpha(0.03), repeat: 10, orientation: C.StripeOrientation.HORIZONTAL }),
        outline: true, outlineColor: new C.CallbackProperty(() => c.withAlpha(reduceMotion() ? 0.9 : 0.55 + 0.4 * Math.abs(Math.sin(now() * 1.6 + idx))), false),
        closeTop: false, closeBottom: false } }))
      tag(v.entities.add({ position: C.Cartesian3.fromDegrees(d.lon, d.lat, h + tall + 4), label: { text: `${DMG_LABEL[d.damage_class]} · ${d.evidence}`, font: '600 12px Inter, sans-serif',
        fillColor: c, showBackground: true, backgroundColor: css('rgba(10,13,15,0.85)'), backgroundPadding: new C.Cartesian2(8, 5), horizontalOrigin: C.HorizontalOrigin.CENTER,
        verticalOrigin: C.VerticalOrigin.BOTTOM, disableDepthTestDistance: Number.POSITIVE_INFINITY, distanceDisplayCondition: new C.DistanceDisplayCondition(0, 1400) } }))
      // both radii read the same frame time, so they are always equal (Cesium rejects minor > major)
      const r0 = d.size_m * 0.6, epoch = v.clock.startTime
      const ph = (t?: C.JulianDate) => (reduceMotion() ? 0.4 : ((t ? C.JulianDate.secondsDifference(t, epoch) : now()) * 0.45 + idx * 0.3) % 1)
      const radius = new C.CallbackProperty(t => r0 + ph(t) * d.size_m * 1.6, false)
      tag(v.entities.add({ position: C.Cartesian3.fromDegrees(d.lon, d.lat), ellipse: {
        semiMajorAxis: radius, semiMinorAxis: radius,
        classificationType: C.ClassificationType.BOTH,
        material: new C.ImageMaterialProperty({ image: im.ring, transparent: true, color: new C.CallbackProperty(t => c.withAlpha(reduceMotion() ? 0.35 : 0.75 * (1 - ph(t))), false) }) } }))
      if (tall > 16) this.addFx(v, new C.ParticleSystem({ image: im.dust, modelMatrix: this.frameAt(d.lon, d.lat, h + 1), emitter: new C.BoxEmitter(new C.Cartesian3(d.size_m * 0.8, d.size_m * 0.8, 4)),
        emissionRate: 5, startColor: C.Color.fromBytes(175, 155, 125, 70), endColor: C.Color.fromBytes(160, 145, 120, 0), startScale: 1, endScale: 2.6,
        minimumParticleLife: 5, maximumParticleLife: 9, minimumSpeed: 0.3, maximumSpeed: 1.1, minimumImageSize: new C.Cartesian2(10, 10), maximumImageSize: new C.Cartesian2(20, 20), sizeInMeters: true }), 'damage', p)
    })
    this.data.fires.forEach(f => this.makeFire(v, f))
  }
  /** Fire at a real fire point: white core, flame body, tongues, embers, smoke + plume with wind gusts, flickering glow (illustrative). */
  private makeFire(v: C.Viewer, f: Fire) {
    const im = fxImages(), now = this.now, h = f.h || 0, p = passIndex(this.data, f.pass_id)
    const enu = this.frameAt(f.lon, f.lat, h + 0.5)
    const wind = C.Matrix4.multiplyByPointAsVector(enu, new C.Cartesian3(3.2, 1.2, 0), new C.Cartesian3())
    const up = C.Matrix4.multiplyByPointAsVector(enu, new C.Cartesian3(0, 0, 1), new C.Cartesian3())
    const tmp = new C.Cartesian3(), tmp2 = new C.Cartesian3(), sw = new C.Cartesian3(), off = (f.lon * 37) % 6.28
    let seed = Math.abs(Math.sin(f.lon * 1e3)) % 1
    const rnd = () => (seed = ((seed * 9301 + 49297) % 233280) / 233280) - 0.5
    const gust = () => (reduceMotion() ? 1 : 1 + 0.9 * Math.sin(now() * 0.55 + off) * (0.6 + 0.4 * Math.sin(now() * 0.21 + off)))
    const swirl = (pt: Particle, dt: number, k: number) => {
      const a = now() * 1.3 + (pt._age || 0) * 0.9 + off
      C.Cartesian3.add(pt.velocity, C.Cartesian3.multiplyByScalar(C.Matrix4.multiplyByPointAsVector(enu, new C.Cartesian3(Math.cos(a), Math.sin(a), 0.15), sw), k * dt, sw), pt.velocity)
    }
    const sway = (k: number) => (pt: C.Particle, dt: number) => {
      C.Cartesian3.add(pt.velocity, C.Cartesian3.multiplyByScalar(up, dt * k, tmp), pt.velocity)
      C.Cartesian3.add(pt.velocity, C.Matrix4.multiplyByPointAsVector(enu, new C.Cartesian3(rnd() * dt * 5, rnd() * dt * 5, 0), tmp2), pt.velocity)
    }
    const P = (o: ConstructorParameters<typeof C.ParticleSystem>[0]) => this.addFx(v, new C.ParticleSystem({ modelMatrix: enu, sizeInMeters: true, ...o }), 'fires', p)
    const S2 = (a: number, b: number) => new C.Cartesian2(a, b)
    P({ image: im.core, emitter: new C.CircleEmitter(4), emissionRate: 90, startColor: C.Color.fromBytes(255, 250, 225, 255), endColor: C.Color.fromBytes(255, 170, 60, 0), startScale: 1, endScale: 0.35,
      minimumParticleLife: 0.4, maximumParticleLife: 0.9, minimumSpeed: 4, maximumSpeed: 8, minimumImageSize: S2(6, 8), maximumImageSize: S2(10, 13), updateCallback: sway(6) })
    const body = P({ image: im.flame, emitter: new C.CircleEmitter(8), emissionRate: 140, startColor: C.Color.fromBytes(255, 195, 95, 240), endColor: C.Color.fromBytes(210, 45, 12, 0), startScale: 1.15, endScale: 0.25,
      minimumParticleLife: 0.8, maximumParticleLife: 1.9, minimumSpeed: 5, maximumSpeed: 11, minimumImageSize: S2(12, 16), maximumImageSize: S2(20, 28), updateCallback: sway(5) })
    const tongues = P({ image: im.flame, emitter: new C.CircleEmitter(5), emissionRate: 28, startColor: C.Color.fromBytes(255, 150, 50, 220), endColor: C.Color.fromBytes(160, 30, 10, 0), startScale: 0.9, endScale: 0.15,
      minimumParticleLife: 1.4, maximumParticleLife: 2.4, minimumSpeed: 9, maximumSpeed: 15, minimumImageSize: S2(8, 18), maximumImageSize: S2(12, 26), updateCallback: sway(4) })
    P({ image: im.ember, emitter: new C.ConeEmitter(C.Math.toRadians(35)), emissionRate: 55, startColor: C.Color.fromBytes(255, 225, 160, 255), endColor: C.Color.fromBytes(255, 90, 30, 0), startScale: 1, endScale: 0.3,
      minimumParticleLife: 2.5, maximumParticleLife: 6, minimumSpeed: 8, maximumSpeed: 18, minimumImageSize: S2(0.9, 0.9), maximumImageSize: S2(1.8, 1.8),
      updateCallback: (pt, dt) => { C.Cartesian3.add(pt.velocity, C.Cartesian3.multiplyByScalar(wind, dt * 0.9 * gust(), tmp), pt.velocity)
        C.Cartesian3.add(pt.velocity, C.Matrix4.multiplyByPointAsVector(enu, new C.Cartesian3(rnd() * dt * 14, rnd() * dt * 14, rnd() * dt * 5), tmp2), pt.velocity) } })
    P({ image: im.smoke, emitterModelMatrix: C.Matrix4.fromTranslation(new C.Cartesian3(0, 0, 18)), emitter: new C.CircleEmitter(8), emissionRate: 12,
      startColor: C.Color.fromBytes(42, 39, 36, 150), endColor: C.Color.fromBytes(90, 86, 82, 0), startScale: 1, endScale: 3.6, minimumParticleLife: 9, maximumParticleLife: 14, minimumSpeed: 9, maximumSpeed: 14,
      minimumImageSize: S2(14, 14), maximumImageSize: S2(22, 22),
      updateCallback: (pt, dt) => { C.Cartesian3.add(pt.velocity, C.Cartesian3.multiplyByScalar(wind, dt * 1.1 * gust(), tmp), pt.velocity); swirl(pt, dt, 7); C.Cartesian3.multiplyByScalar(pt.velocity, 1 - dt * 0.06, pt.velocity) } })
    P({ image: im.smoke, emitterModelMatrix: C.Matrix4.fromTranslation(new C.Cartesian3(0, 0, 40)), emitter: new C.CircleEmitter(12), emissionRate: 4,
      startColor: C.Color.fromBytes(100, 95, 90, 70), endColor: C.Color.fromBytes(150, 146, 140, 0), startScale: 1.5, endScale: 7, minimumParticleLife: 16, maximumParticleLife: 26, minimumSpeed: 4, maximumSpeed: 7,
      minimumImageSize: S2(20, 20), maximumImageSize: S2(32, 32),
      updateCallback: (pt, dt) => { C.Cartesian3.add(pt.velocity, C.Cartesian3.multiplyByScalar(wind, dt * 1.6 * gust(), tmp), pt.velocity); swirl(pt, dt, 5) } })
    // flames breathe: emission pulses so the fire flares and dies back
    v.scene.preRender.addEventListener(() => {
      if (!body.show || reduceMotion()) return
      const t = now() + off, k = 0.75 + 0.3 * Math.sin(t * 3.1) + 0.2 * Math.sin(t * 7.7) + 0.12 * Math.sin(t * 13.3)
      body.emissionRate = 140 * k; tongues.emissionRate = 28 * Math.max(0.2, k * k)
    })
    const flick = () => (reduceMotion() ? 0.5 : 0.45 + 0.13 * Math.sin(now() * 7.3) + 0.09 * Math.sin(now() * 12.9 + 1.3) + 0.05 * Math.sin(now() * 23.1))
    const tag = (e: C.Entity) => { const t = e as Tagged; t._layer = 'fires'; t._pass = p }
    tag(v.entities.add({ position: C.Cartesian3.fromDegrees(f.lon, f.lat), ellipse: { semiMajorAxis: 110, semiMinorAxis: 110, classificationType: C.ClassificationType.BOTH,
      material: new C.ImageMaterialProperty({ image: im.glow, transparent: true, color: new C.CallbackProperty(() => C.Color.WHITE.withAlpha(flick()), false) }) } }))
    tag(v.entities.add({ position: C.Cartesian3.fromDegrees(f.lon, f.lat, h + 12), billboard: { image: im.glow, sizeInMeters: true, width: 80, height: 80,
      color: new C.CallbackProperty(() => C.Color.WHITE.withAlpha(flick() * 0.55), false) } }))
  }

  /* ---------- per frame ---------- */
  private tick(v: C.Viewer) {
    const h = v.camera.positionCartographic.height
    if (this.tileset && this.layers.buildings) {
      // progressive reveal: buildings fade in and sharpen as the camera descends
      const a = h > 14000 ? 0 : h < 3500 ? 1 : Math.round((1 - (h - 3500) / 10500) * 4) / 4
      if (a !== this.tileset._alpha) { this.tileset._alpha = a; this.tileset.style = buildingStyle(a) }
      this.tileset.maximumScreenSpaceError = h > 8000 ? 32 : h > 2500 ? 16 : 6
    }
    if (this.flying) this.setPhase(h > 22000 ? 1 : h > 2600 ? 2 : 3)
    const o = this.orbitT
    if (o) {
      // time-based: same angular speed at any frame rate; gentle ease-in for the first second
      const t = performance.now(), dt = Math.min(0.1, (t - o.last) / 1000); o.last = t
      const done = 2 * Math.PI - o.left, ease = isFinite(o.left) ? Math.min(1, 0.25 + done / 0.6) : 1
      const step = o.speed * dt * ease * (reduceMotion() ? 0.5 : 1)
      o.heading += step; o.left -= step
      v.camera.lookAt(o.target, new C.HeadingPitchRange(o.heading, o.pitch, o.range))
      if (o.left <= 0) this.stopOrbit()
    }
  }
  private setPhase(p: number) { if (p !== this.phase) { this.phase = p; this.ev.phase(p) } }

  /* ---------- picking ---------- */
  private pickHandler(v: C.Viewer) {
    const h = new C.ScreenSpaceEventHandler(v.scene.canvas)
    h.setInputAction(() => this.stopOrbit(), C.ScreenSpaceEventType.LEFT_DOWN)
    h.setInputAction(() => this.stopOrbit(), C.ScreenSpaceEventType.WHEEL)
    h.setInputAction((e: { position: C.Cartesian2 }) => {
      const p = v.scene.pick(e.position)
      const id = p && (p.id as Tagged | undefined)
      if (id && id._incident) return this.ev.pickIncident(id._incident)
      if (id && id._shelter) return this.ev.pickShelter(id._shelter)
      if (p instanceof C.Cesium3DTileFeature) this.ev.pickBuilding(this.buildingInfo(p, v.scene.pickPosition(e.position)))
    }, C.ScreenSpaceEventType.LEFT_CLICK)
    h.setInputAction((e: { endPosition: C.Cartesian2 }) => {
      const p = v.scene.pick(e.endPosition), id = p && (p.id as Tagged | undefined)
      v.canvas.style.cursor = id && (id._incident || id._shelter) ? 'pointer' : ''
    }, C.ScreenSpaceEventType.MOUSE_MOVE)
  }
  private buildingInfo(f: C.Cesium3DTileFeature, pos?: C.Cartesian3): BuildingInfo {
    const g = (k: string) => { try { const x = f.getProperty(k); return x === undefined || x === null || x === '' ? null : String(x) } catch { return null } }
    const tagH = parseFloat(g('height') ?? ''), estH = parseFloat(g('cesium#estimatedHeight') ?? '')
    const H = isFinite(tagH) ? tagH : estH, estimated = !isFinite(tagH), levels = parseFloat(g('building:levels') ?? '')
    let cell: BuildingInfo['cell'] = null
    if (pos) {
      const c = C.Cartographic.fromCartesian(pos), pt = { lon: C.Math.toDegrees(c.longitude), lat: C.Math.toDegrees(c.latitude) }
      cell = this.data.damage_cells.find(d => dist(d, pt) < d.size_m * 0.7 && visibleAt(this.data, this.passIdx)(d)) ?? null
    }
    const fl = isFinite(levels) ? [levels, levels] : isFinite(H) ? [Math.max(1, Math.floor(H / 3.4)), Math.max(1, Math.ceil(H / 2.9))] : null
    const use = g('building') || 'unknown'
    if (this.edge) this.edge.selected = [f as unknown as C.Primitive]
    return {
      name: g('name') || 'Unnamed building', id: g('elementId') || g('id') || '—', use, material: g('building:material'),
      height: isFinite(H) ? `${Math.round(H * 0.85)}–${Math.round(H * 1.15)} m${estimated ? ' (estimated)' : ''}` : 'Unknown',
      floors: fl ? `${fl[0]}–${fl[1]}` : 'Unknown', facility: /hospital|clinic|school|university/.test(use) || !!g('amenity'),
      residents: fl && /house|residential|apartments|yes/.test(use === 'unknown' ? 'yes' : use) ? `${fl[0] * 2}–${fl[1] * 5} (sample model)` : '—', cell,
    }
  }
  clearBuildingHighlight() { if (this.edge) this.edge.selected = [] }

  /* ---------- state from React ---------- */
  refresh() {
    const vis = (en: Tagged) => {
      if (en._incident) return (en._pass ?? 0) <= this.passIdx
      if (en._layer === 'shelters') return this.layers.shelters && (!en._forIncident || en._forIncident === this.selected)
      const on = this.layers[en._layer as keyof Layers]
      return on !== false && (en._pass === undefined || en._pass <= this.passIdx)
    }
    ;[this.v3, this.v2].forEach(v => {
      if (!v) return
      ;(v.entities.values as Tagged[]).forEach(en => { if (en._layer) en.show = vis(en) })
      ;(this.overlays.get(v) ?? []).forEach(l => { l.show = this.layers.streets })
    })
    this.fx.forEach(p => { p.show = this.layers[p._layer] && p._pass <= this.passIdx })
    if (this.tileset) this.tileset.show = this.layers.buildings
  }
  setLayers(l: Layers) { this.layers = { ...l }; this.refresh() }
  setPass(i: number) { this.passIdx = i; [this.v3, this.v2].forEach(v => v && this.drawPaths(v)); this.refresh() }
  setSelected(id: string | null) { this.selected = id; this.refresh() }
  setBase(b: BaseMap) { this.base = b; [this.v3, this.v2].forEach(v => v && this.setupImagery(v)); this.refresh() }
  setMode(m: ViewMode) { this.mode = m; if (m === '2d') this.stopOrbit() }
  pathFor(shelterId: string) { return this.paths.find(p => p.shelter_id === shelterId) }
  pathById(id: string) { return this.paths.find(p => p.id === id) }

  /* ---------- camera ----------
     Rules: one flight at a time (a newer flight cancels the older one), no jumps, time-based motion
     (same speed at any frame rate), and after arriving the camera stays anchored on the incident so
     drag orbits around it and scroll zooms towards it. */
  private flightId = 0
  private anchorTarget: C.Cartesian3 | null = null
  /** Keeps the camera where it is but makes the target the centre of drag/zoom. */
  private anchor(target: C.Cartesian3) {
    const v = this.v3; if (!v) return
    const range = C.Cartesian3.distance(v.camera.positionWC, target)
    v.camera.lookAtTransform(C.Transforms.eastNorthUpToFixedFrame(target), new C.HeadingPitchRange(v.camera.heading, v.camera.pitch, range))
    this.anchorTarget = target
  }
  private release() {
    if (!this.anchorTarget && !this.orbitT) return
    this.orbitT = null; this.anchorTarget = null
    this.v3?.camera.lookAtTransform(C.Matrix4.IDENTITY)
    this.ev.orbit(false)
  }
  private startFlight() { this.release(); this.clearBuildingHighlight(); this.v3?.camera.cancelFlight(); return ++this.flightId }
  private fly(opts: Parameters<C.Camera['flyToBoundingSphere']>[1] & { sphere: C.BoundingSphere }) {
    return new Promise<void>(r => this.v3!.camera.flyToBoundingSphere(opts.sphere, { ...opts, complete: r, cancel: r }))
  }

  flyBird(duration = reduceMotion() ? 0 : 3.5) {
    const id = this.startFlight(), v = this.v3; if (!v) return
    this.flying = true; this.setPhase(1)
    v.camera.flyTo({ destination: C.Cartesian3.fromDegrees(BIRD.lon, BIRD.lat, BIRD.h), orientation: { heading: C.Math.toRadians(BIRD.heading), pitch: C.Math.toRadians(BIRD.pitch), roll: 0 },
      duration, easingFunction: C.EasingFunction.QUINTIC_IN_OUT, complete: () => { if (id === this.flightId) { this.flying = false; this.setPhase(1) } } })
    this.v2?.camera.flyTo({ destination: REGION(), duration: reduceMotion() ? 0 : 1.5 })
  }
  /** Regional → descent → arrival → one slow 360° turn around the incident, then anchored. */
  async flyToIncident(inc: Incident) {
    const id = this.startFlight()
    this.v2?.camera.flyTo({ destination: C.Cartesian3.fromDegrees(inc.lon, inc.lat, 2600), duration: reduceMotion() ? 0 : 2 })
    const v = this.v3; if (!v || this.mode === '2d') return
    await this.heightsReady
    if (id !== this.flightId) return
    const target = C.Cartesian3.fromDegrees(inc.lon, inc.lat, inc.h || 0), sphere = new C.BoundingSphere(target, 1)
    const heading = C.Math.toRadians(inc.rank % 2 ? 32 : -28), pitch = C.Math.toRadians(-27), off = new C.HeadingPitchRange(heading, pitch, 820)
    if (reduceMotion()) { v.camera.lookAt(target, off); this.anchorTarget = target; this.flying = false; this.setPhase(3); return }
    this.flying = true
    // Phase 1: if already low (e.g. at another incident) rise to a regional view first, so we never skim through terrain
    if (v.camera.positionCartographic.height < 9000) {
      this.setPhase(1)
      await this.fly({ sphere, offset: new C.HeadingPitchRange(heading - C.Math.toRadians(30), C.Math.toRadians(-50), 26000), duration: 3, easingFunction: C.EasingFunction.SINUSOIDAL_IN_OUT })
      if (id !== this.flightId) return
    }
    // Phases 2-3: one continuous eased descent with a slow arrival
    await this.fly({ sphere, offset: off, duration: 7.5, easingFunction: cinematic, maximumHeight: 30000 })
    if (id !== this.flightId) return
    this.flying = false; this.setPhase(3)
    this.anchor(target)
    // Phase 4: one full slow turn around the place, then stop and stay anchored
    this.orbitT = { target, range: 820, pitch, heading, speed: (2 * Math.PI) / 30, left: 2 * Math.PI, last: performance.now(), arrival: true }
    this.setPhase(4); this.ev.orbit(true)
  }
  /** Frames a set of points in both views. */
  showOnMap(points: LonLat[]) {
    if (!points.length) return
    const id = this.startFlight()
    this.heightsReady.then(() => {
      if (id !== this.flightId) return
      const bs = C.BoundingSphere.fromPoints(points.map(p => C.Cartesian3.fromDegrees(p.lon, p.lat, p.h || 0))); bs.radius = Math.max(bs.radius, 150)
      const dur = reduceMotion() ? 0 : 2.2
      if (this.v3 && this.mode !== '2d') this.v3.camera.flyToBoundingSphere(bs, { offset: new C.HeadingPitchRange(this.v3.camera.heading, C.Math.toRadians(-48), bs.radius * 3.4), duration: dur, easingFunction: C.EasingFunction.QUADRATIC_IN_OUT })
      const c = C.Cartographic.fromCartesian(bs.center)
      this.v2?.camera.flyTo({ destination: C.Cartesian3.fromDegrees(C.Math.toDegrees(c.longitude), C.Math.toDegrees(c.latitude), bs.radius * 5), duration: dur })
    })
  }
  /** Orbit 360 button: continuous slow turn around the selected incident (or the screen centre). Returns true when orbiting. */
  toggleOrbit(): boolean {
    if (this.orbitT) { this.stopOrbit(); return false }
    const v = this.v3; if (!v || this.mode === '2d') return false
    const inc = this.data.incidents.find(i => i.id === this.selected)
    let target = this.anchorTarget ?? undefined
    if (!target && inc) target = C.Cartesian3.fromDegrees(inc.lon, inc.lat, inc.h || 0)
    if (!target) { const ray = v.camera.getPickRay(new C.Cartesian2(v.canvas.clientWidth / 2, v.canvas.clientHeight / 2)); target = ray && v.scene.globe.pick(ray, v.scene) }
    if (!target) return false
    v.camera.cancelFlight(); this.flying = false
    const range = C.Cartesian3.distance(v.camera.positionWC, target)
    // read heading/pitch relative to the target so the turn starts exactly where the camera is (no jump)
    this.anchor(target)
    this.orbitT = { target, range, pitch: Math.min(v.camera.pitch, C.Math.toRadians(-12)), heading: v.camera.heading, speed: (2 * Math.PI) / 40, left: Infinity, last: performance.now(), arrival: false }
    this.ev.orbit(true)
    return true
  }
  /** Stops turning but keeps the camera anchored on the place. */
  stopOrbit() {
    if (!this.orbitT) return
    const wasArrival = this.orbitT.arrival
    this.orbitT = null; this.ev.orbit(false)
    if (wasArrival) this.setPhase(3)
  }
}
