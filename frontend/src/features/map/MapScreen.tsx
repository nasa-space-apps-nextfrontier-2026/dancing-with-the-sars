import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { BaseMap, Incident, LayerKey, Layers, LonLat, MapData, ViewMode } from '../../types/map'
import { api, type Session } from '../../services/api'
import { Icon, Logo, type IconName } from '../../components/Icons'
import { MapEngine, type BuildingInfo } from './engine'
import { passIndex } from './analysis'
import { LeftPanel, Legend, RightPanel, type LeftKey, type RightView } from './panels'

const DEFAULT_LAYERS: Layers = { damage: true, second: true, change: false, fires: true, night: false, pop: false, facilities: true, shelters: true, routes: true, streets: true, buildings: true }
const TOKEN_KEY = 'civisar.ionToken'
function storedToken(): string | null {
  const env = import.meta.env.VITE_CESIUM_ION_TOKEN as string | undefined
  if (env) return env
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}

export type MapCtx = {
  data: MapData; passIdx: number; layers: Layers; selected: Incident | null; engine: MapEngine | null; roadsVersion: number
  selectIncident: (id: string, fly: boolean) => void; openShelter: (id: string) => void; showOnMap: (pts: LonLat[], layers?: LayerKey[]) => void
  setLayer: (k: LayerKey, on: boolean) => void; openLeft: (k: LeftKey | null) => void
}

export function MapScreen({ session, onSignOut }: { session: Session; onSignOut: () => void }) {
  const [data, setData] = useState<MapData | null>(null)
  const [loadError, setLoadError] = useState('')
  const [token, setToken] = useState<string | null | undefined>(() => storedToken() ?? undefined) // undefined = not asked yet
  const [layers, setLayers] = useState<Layers>(DEFAULT_LAYERS)
  const [passIdx, setPassIdx] = useState(4)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [mode, setMode] = useState<ViewMode>('3d')
  const [base, setBase] = useState<BaseMap>('sat')
  const [focus, setFocus] = useState(false)
  const [left, setLeft] = useState<LeftKey | null>(null)
  const [rightOpen, setRightOpen] = useState(true)
  const [rightView, setRightView] = useState<RightView>({ kind: 'incident' })
  const [legend, setLegend] = useState(false)
  const [phase, setPhase] = useState(0)
  const [orbit, setOrbit] = useState(false)
  const [banner, setBanner] = useState('')
  const [roadsVersion, setRoadsVersion] = useState(0)
  const [menu, setMenu] = useState(false)
  const engineRef = useRef<MapEngine | null>(null)
  const v3Ref = useRef<HTMLDivElement>(null), v2Ref = useRef<HTMLDivElement>(null), creditRef = useRef<HTMLSpanElement>(null)
  const [, force] = useState(0)

  useEffect(() => { api.mapData().then(r => setData(r.data)).catch(e => setLoadError(String(e.message || e))) }, [])
  useEffect(() => { document.body.className = `mode-${mode}${focus ? ' focus' : ''}`; return () => { document.body.className = '' } }, [mode, focus])
  useEffect(() => { if (!banner) return; const t = setTimeout(() => setBanner(''), 9000); return () => clearTimeout(t) }, [banner])

  const selected = useMemo(() => data?.incidents.find(i => i.id === selectedId) ?? null, [data, selectedId])

  const selectIncident = useCallback((id: string, fly: boolean) => {
    const e = engineRef.current, inc = data?.incidents.find(i => i.id === id); if (!inc) return
    setSelectedId(id); setRightView({ kind: 'incident' }); setRightOpen(true)
    e?.setSelected(id); e?.clearBuildingHighlight()
    if (fly) e?.flyToIncident(inc)
  }, [data])
  const showOnMap = useCallback((pts: LonLat[], keys: LayerKey[] = []) => {
    if (keys.length) setLayers(l => { const n = { ...l }; keys.forEach(k => { n[k] = true }); engineRef.current?.setLayers(n); return n })
    engineRef.current?.showOnMap(pts)
  }, [])
  const openShelter = useCallback((id: string) => {
    const sh = data?.shelters.find(s => s.id === id), e = engineRef.current; if (!sh || !data) return
    const inc = data.incidents.find(i => i.id === sh.incident_id)!
    setSelectedId(sh.incident_id); e?.setSelected(sh.incident_id)
    setRightView({ kind: 'shelter', id }); setRightOpen(true)
    const st = e?.pathFor(id)
    showOnMap([...(st ? st.coords.map(([lon, lat]) => ({ lon, lat })) : []), sh, inc], ['shelters'])
  }, [data, showOnMap])

  // engine lifecycle: once data is loaded and the token question is answered
  const handlers = useRef({ selectIncident, openShelter })
  handlers.current = { selectIncident, openShelter }
  useEffect(() => {
    if (!data || token === undefined || !v3Ref.current || !creditRef.current) return
    const e = new MapEngine(data, token, {
      phase: setPhase,
      pickIncident: id => handlers.current.selectIncident(id, true),
      pickShelter: id => handlers.current.openShelter(id),
      pickBuilding: (b: BuildingInfo) => { setRightView({ kind: 'building', info: b }); setRightOpen(true) },
      banner: setBanner,
      roads: () => setRoadsVersion(v => v + 1),
      orbit: setOrbit,
    }, DEFAULT_LAYERS, 4)
    engineRef.current = e
    try { e.mount3d(v3Ref.current, creditRef.current) }
    catch (err) { console.warn(err); setMode('2d'); setBanner('3D could not start on this device. Showing the 2D map.') }
    if (!token) setBanner('Running without a Cesium token: flat ground, no 3D buildings. Effects and panels still work.')
    force(x => x + 1)
    return () => { e.destroy(); engineRef.current = null }
  }, [data, token])

  // keep engine in sync with React state
  useEffect(() => { engineRef.current?.setLayers(layers) }, [layers])
  useEffect(() => { engineRef.current?.setPass(passIdx) }, [passIdx])
  useEffect(() => { engineRef.current?.setBase(base) }, [base])
  useEffect(() => {
    const e = engineRef.current; if (!e) return
    e.setMode(mode)
    if ((mode === '2d' || mode === 'split') && v2Ref.current) {
      try { e.mount2d(v2Ref.current) } catch (err) { console.warn(err); setBanner('The 2D map could not start on this device.') }
    }
  }, [mode, roadsVersion])

  if (loadError) return <main className="signin"><div className="signin-card glass"><h1>Map data could not load</h1><p className="muted small">{loadError}</p></div></main>
  if (!data) return <main className="signin"><span className="muted small">Loading map…</span></main>

  const ctx: MapCtx = { data, passIdx, layers, selected, engine: engineRef.current, roadsVersion, selectIncident, openShelter, showOnMap,
    setLayer: (k, on) => setLayers(l => ({ ...l, [k]: on })), openLeft: setLeft }
  const pass = data.passes[passIdx], n = data.passes.length - 1
  const flyTop = () => { const top = [...data.incidents].filter(i => passIndex(data, i.first_pass) <= passIdx).sort((a, b) => a.rank - b.rank)[0]; if (top) selectIncident(top.id, true) }
  const rail: [LeftKey | 'incident', string, IconName][] = [['incident', 'Incident', 'incident'], ['rank', 'Incident ranking', 'rank'], ['decide', 'Decision assistant', 'decide'], ['budget', 'Rebuild budget', 'budget'], ['layers', 'Layers', 'layers']]
  const initials = session.user_id.replace(/[^a-z]/gi, '').slice(0, 2).toUpperCase() || 'U'
  const credit = base === 'streets' ? 'Map: © OpenStreetMap contributors'
    : `Imagery: Esri World Imagery · capture date varies by tile, not the incident date${layers.streets ? ' · Streets: Esri' : ''}${engineRef.current?.roadsLoaded ? ' · Routing: OSRM, © OpenStreetMap' : ''}`

  return <>
    <div id="scene">
      <div id="v3wrap"><div ref={v3Ref} style={{ position: 'absolute', inset: 0 }} /><div className="viewlabel glass">3D</div></div>
      <div id="v2wrap"><div ref={v2Ref} style={{ position: 'absolute', inset: 0 }} /><div className="viewlabel glass">2D</div></div>
    </div>
    <div id="vig" />

    <header id="top">
      <div className="pill glass brand"><span className="logo"><Logo /></span><b>CIVISAR</b><small>South Lebanon</small></div>
      <nav className="pill glass tabs" aria-label="Pages">
        {(['map', 'alerts', 'areas', 'sources'] as const).map(p => <button key={p} className="tab" aria-current={(p === 'map' && (!left || !left.startsWith('page:'))) || left === `page:${p}` ? 'page' : undefined}
          onClick={() => setLeft(p === 'map' ? null : (`page:${p}` as LeftKey))}>{p[0].toUpperCase() + p.slice(1)}</button>)}
      </nav>
      <div className="spacer" />
      <span className="badge-sample" title="All incidents and values are sample data">Sample data</span>
      <div className="pill glass seg" role="group" aria-label="Base map">
        {([['sat', 'Satellite'], ['streets', 'Streets']] as const).map(([k, t]) => <button key={k} aria-pressed={base === k} onClick={() => setBase(k)}>{t}</button>)}
      </div>
      <div className="pill glass seg" role="group" aria-label="View mode">
        {([['2d', '2D'], ['3d', '3D'], ['split', 'Split']] as const).map(([k, t]) => <button key={k} aria-pressed={mode === k} onClick={() => setMode(k)}>{t}</button>)}
      </div>
      <button className="btn glass top-btn" aria-pressed={focus} onClick={() => setFocus(f => !f)}>Focus</button>
      <button className="btn primary top-btn" id="flyTop" onClick={flyTop}><Icon name="plane" size={16} /><span>Fly to top incident</span></button>
      <div className="usermenu">
        <button className="avatar" aria-haspopup="menu" aria-expanded={menu} onClick={() => setMenu(m => !m)} title="Account">{initials}</button>
        {menu && <div className="menu glass" role="menu">
          <div className="who"><b>{session.user_id}</b>{session.role}{session.demo ? ' · demo session' : ''}</div>
          <button className="btn ghost sm" role="menuitem" onClick={() => { setMenu(false); try { localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ } setToken(null) }}>Forget Cesium token</button>
          <button className="btn ghost sm" role="menuitem" onClick={onSignOut}>Sign out</button>
        </div>}
      </div>
    </header>

    <nav id="rail" className="glass" aria-label="Panels">
      {rail.map(([k, t, ic]) => {
        const on = k === 'incident' ? rightOpen : left === k
        return <button key={k} className="rb" aria-label={t} aria-pressed={on} onClick={() => k === 'incident' ? (setRightView({ kind: 'incident' }), setRightOpen(o => !o)) : setLeft(left === k ? null : k)}>
          <Icon name={ic} size={21} /><span className="tip">{t}</span></button>
      })}
      <div className="rail-sep" />
      <button className="rb" aria-label="Legend" aria-pressed={legend} onClick={() => setLegend(l => !l)}><Icon name="legend" size={21} /><span className="tip">Legend</span></button>
    </nav>

    <LeftPanel ctx={ctx} k={left} onClose={() => setLeft(null)} />
    <RightPanel ctx={ctx} open={rightOpen} view={rightView} setView={setRightView} onClose={() => { setRightOpen(false); engineRef.current?.clearBuildingHighlight() }} />
    {legend && <Legend onClose={() => setLegend(false)} />}
    {banner && <div id="banner" className="glass" style={{ display: 'block' }} role="status">{banner}</div>}
    <button className="btn glass" id="exitFocus" onClick={() => setFocus(false)}>Exit focus</button>
    <div id="credit"><span>{credit}</span> · <span id="ccx" ref={creditRef} /></div>

    <footer id="dock" className="glass">
      <div className="phases hide-in-focus" aria-live="polite">
        <div className="lab">Camera flight</div>
        <div className="steps">{['Regional', 'Descent', 'Arrival', '360° view'].map((t, i) => <div key={t} className={`step${phase === i + 1 ? ' on' : phase > i + 1 ? ' done' : ''}`}>{t}</div>)}</div>
      </div>
      <div className="timeline">
        <div className="tl-head"><span>Satellite pass&nbsp; <b>{pass.date} · {pass.sensor}</b></span><span>{pass.status === 'missed' ? 'Missed pass · no new data from this date' : 'Building changes appear 72 h after the pass'}</span></div>
        <div className="track">
          <div className="rl" /><div className="fill" style={{ width: `${(passIdx / n) * 100}%` }} />
          <input type="range" min={0} max={n} step={1} value={passIdx} onChange={e => setPassIdx(+e.target.value)} aria-label="Satellite pass date" />
          {data.passes.map((p, i) => <div key={p.id} className={`tick${p.status === 'missed' ? ' missed' : ''}${i === passIdx ? ' cur' : ''}`} style={{ left: `${(i / n) * 100}%` }} title={p.status === 'missed' ? 'Missed pass' : p.sensor} />)}
        </div>
        <div className="ticklabels">{data.passes.map((p, i) => <span key={p.id} style={{ left: `${(i / n) * 100}%` }}>{p.date.slice(5).replace('-', '/')}{p.status === 'missed' ? ' · missed' : ''}</span>)}</div>
      </div>
      <div className="camctl">
        <span className="hint">Drag to orbit<br />Scroll to zoom</span>
        <button className="btn" aria-pressed={orbit} onClick={() => setOrbit(engineRef.current?.toggleOrbit() ?? false)}><Icon name="orbit" size={16} />Orbit 360</button>
        <button className="btn" onClick={() => engineRef.current?.flyBird()}>Reset</button>
      </div>
    </footer>

    {token === undefined && <TokenBox onDone={t => { if (t) { try { localStorage.setItem(TOKEN_KEY, t) } catch { /* private mode */ } } setToken(t) }} />}
  </>
}

function TokenBox({ onDone }: { onDone: (t: string | null) => void }) {
  const [v, setV] = useState('')
  return <div id="modal"><div className="mbox glass">
    <span className="kicker">3D setup</span>
    <h1>Add a free Cesium ion token</h1>
    <p className="muted small" style={{ margin: 0 }}>Terrain and OSM 3D buildings come from Cesium ion (free account). The token stays in this browser only. Developers can set <span className="mono">VITE_CESIUM_ION_TOKEN</span> in <span className="mono">frontend/.env.local</span>.</p>
    <ol><li>Sign up free at ion.cesium.com</li><li>Open <b>Access Tokens</b> and copy the Default token</li><li>Paste it below</li></ol>
    <input value={v} onChange={e => setV(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && v.trim()) onDone(v.trim()) }} placeholder="eyJhbGciOi…" autoComplete="off" spellCheck={false} aria-label="Cesium ion token" autoFocus />
    <div className="row" style={{ justifyContent: 'flex-end' }}>
      <button className="btn ghost" onClick={() => onDone(null)}>Continue without 3D buildings</button>
      <button className="btn primary" disabled={!v.trim()} onClick={() => onDone(v.trim())}>Use token</button>
    </div>
  </div></div>
}
