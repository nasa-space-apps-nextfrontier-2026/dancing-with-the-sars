import { useState, type ReactNode } from 'react'
import type { DamageClass, Evidence, LayerKey } from '../../types/map'
import { Icon, type IconName } from '../../components/Icons'
import { addHours, analyse, AREA_M, dist, dms, fmtM, passIndex, pathStats, rng, type Hazard } from './analysis'
import { DMG_LABEL, type BuildingInfo } from './engine'
import type { MapCtx } from './MapScreen'

export type LeftKey = 'rank' | 'decide' | 'budget' | 'layers' | 'page:alerts' | 'page:areas' | 'page:sources'
export type RightView = { kind: 'incident' } | { kind: 'building'; info: BuildingInfo } | { kind: 'shelter'; id: string }
type Tab = 'summary' | 'impacts' | 'shelters' | 'power' | 'insights'

/* ---------- atoms ---------- */
export const Ev = ({ e }: { e: Evidence }) => <span className={`chip ev-${e}`}>{e}</span>
export const Dmg = ({ d }: { d: DamageClass }) => <span className="dchip"><span className={`hatch d-${d}`} />{DMG_LABEL[d]}</span>
const Note = ({ children }: { children: ReactNode }) => <div className="note"><Icon name="info" size={16} /><span>{children}</span></div>
function Head({ kicker, title, onClose }: { kicker: string; title: string; onClose: () => void }) {
  return <div className="dh"><div style={{ flex: 1, minWidth: 0 }}><span className="kicker">{kicker}</span><h2>{title}</h2></div>
    <button className="x" aria-label="Close panel" onClick={onClose}><Icon name="close" size={20} /></button></div>
}
const KBtn = ({ label, onClick, icon = 'pin' }: { label: string; onClick: () => void; icon?: IconName }) =>
  <button className="kbtn" title={label} aria-label={label} onClick={onClick}><Icon name={icon} size={12} /></button>
function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false)
  return <button className="kbtn" style={done ? { color: 'var(--ev-corroborated)' } : undefined} title={done ? 'Copied' : 'Copy'} aria-label={`Copy ${text}`}
    onClick={async () => { try { await navigator.clipboard.writeText(text); setDone(true) } catch { /* clipboard blocked */ } }}><Icon name="copy" size={12} /></button>
}
function HzTags({ hz }: { hz: Hazard[] }) {
  return <>{hz.map((h, i) => h.kind === 'damage' ? <span key={i} className="tag warn">{h.inside ? 'Inside' : 'Near'} damage area{h.inside ? '' : ` · ${h.m} m`}</span>
    : h.kind === 'fire' ? <span key={i} className="tag fire">Within fire ring · {h.m} m</span>
      : <span key={i} className="tag pw">{h.inside ? 'Inside' : 'Near'} possible power loss</span>)}</>
}

/* ---------- legend ---------- */
export function Legend({ onClose }: { onClose: () => void }) {
  return <div id="legend" className="glass" role="dialog" aria-label="Legend">
    <div className="row" style={{ justifyContent: 'space-between' }}><span className="kicker" style={{ margin: 0 }}>Legend</span>
      <button className="x" aria-label="Close legend" onClick={onClose}><Icon name="close" size={18} /></button></div>
    <ul>
      <li><svg className="lg" viewBox="0 0 28 16"><defs><pattern id="lh" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2" height="5" fill="#f5904f" /></pattern></defs><rect x="1" y="1" width="26" height="14" rx="3" fill="url(#lh)" stroke="#f5904f" strokeWidth="1.5" /></svg>Damage candidate (colour = class)</li>
      <li><svg className="lg" viewBox="0 0 28 16"><circle cx="14" cy="8" r="6.5" fill="none" stroke="#45c79c" strokeWidth="2" strokeDasharray="3 2.5" /></svg>Second sensor agrees</li>
      <li><svg className="lg" viewBox="0 0 28 16"><circle cx="14" cy="8" r="6.5" fill="none" stroke="#ff8a4d" strokeWidth="1.6" strokeDasharray="4 2" /><circle cx="14" cy="8" r="2.5" fill="#ff8a4d" /></svg>Fire, 375 m uncertainty ring</li>
      <li><svg className="lg" viewBox="0 0 28 16"><defs><pattern id="ln" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#9d93e6" /></pattern></defs><rect x="1" y="1" width="26" height="14" rx="3" fill="url(#ln)" /></svg>Possible power loss</li>
      <li><svg className="lg" viewBox="0 0 28 16"><path d="M2 8h24" stroke="#0a0d0f" strokeWidth="8" /><path d="M2 8h24" stroke="#f1f4f3" strokeWidth="4" /></svg>Available route, not verified</li>
      <li><svg className="lg" viewBox="0 0 28 16"><path d="M2 8h24" stroke="#ff5a5f" strokeWidth="4" strokeDasharray="6 3" /></svg>Possibly blocked (candidate)</li>
    </ul>
  </div>
}

/* ---------- right panel ---------- */
export function RightPanel({ ctx, open, view, setView, onClose }: { ctx: MapCtx; open: boolean; view: RightView; setView: (v: RightView) => void; onClose: () => void }) {
  const [tab, setTab] = useState<Tab>('summary')
  return <aside id="right" className={`drawer glass${open ? '' : ' hidden'}`} aria-label="Incident">
    {view.kind === 'building' ? <BuildingDetail ctx={ctx} b={view.info} back={() => setView({ kind: 'incident' })} onClose={onClose} />
      : view.kind === 'shelter' ? <ShelterDetail ctx={ctx} id={view.id} back={() => { setView({ kind: 'incident' }); setTab('shelters') }} onClose={onClose} />
        : <IncidentPanel ctx={ctx} tab={tab} setTab={setTab} onClose={onClose} />}
  </aside>
}

function IncidentPanel({ ctx, tab, setTab, onClose }: { ctx: MapCtx; tab: Tab; setTab: (t: Tab) => void; onClose: () => void }) {
  const { data: D, passIdx, selected: inc } = ctx
  if (!inc) {
    const vis = D.incidents.filter(i => passIndex(D, i.first_pass) <= passIdx).length
    return <><Head kicker="Incident" title="No incident selected" onClose={onClose} />
      <div className="db"><p style={{ marginTop: 0 }}>{vis} candidate incidents on this pass. Pick a pin on the map, or use <b>Fly to top incident</b>.</p>
        <Note>Every marker is a candidate from satellite data. Nothing on this map is confirmed on the ground.</Note></div></>
  }
  const A = analyse(D, inc, passIdx), p = D.passes[passIndex(D, inc.first_pass)]
  const tabs: [Tab, string, number?][] = [['summary', 'Summary'], ['impacts', 'Impacts'], ['shelters', 'Shelters', A.shelters.length], ['power', 'Power', A.dark.length], ['insights', 'Insights', inc.insights.length]]
  const show = ctx.showOnMap
  let body: ReactNode
  if (tab === 'summary') {
    const Kpi = ({ icon, k, val, sub, onShow }: { icon: IconName; k: string; val: string | number; sub: string; onShow: () => void }) =>
      <div className="kpi"><span className="k"><Icon name={icon} size={13} />{k}<KBtn label={`Show ${k.toLowerCase()} on map`} onClick={onShow} /></span><b>{val}</b><span className="s">{sub}</span></div>
    body = <>
      <div className="kpis">
        <Kpi icon="people" k="People" val={inc.people_available === false ? 'Unknown' : rng(inc.people_nearby)} sub={inc.people_available === false ? 'Population evidence unavailable' : 'In affected area (WorldPop)'} onShow={() => show([...D.population.filter(c => dist(c, inc) <= AREA_M), inc], ['pop'])} />
        <Kpi icon="facility" k="Facilities" val={A.facilities.length} sub="Inside or near damage, fire or dark cells" onShow={() => show([...A.facilities.map(x => x.f), inc], ['facilities'])} />
        <Kpi icon="road" k="Roads" val={A.roads.length} sub="Possibly blocked (candidate)" onShow={() => show(A.roads.flatMap(r => r.coords.map(([lon, lat]) => ({ lon, lat }))), ['routes'])} />
        <Kpi icon="power" k="Power" val={A.dark.length ? (A.dark.some(cell => cell.people_available === false) ? 'Unknown' : rng(A.darkPeople)) : '0'} sub={A.dark.length ? `People in ${A.dark.length} dark cell${A.dark.length > 1 ? 's' : ''}: possible power loss` : 'No dark cells on this pass'} onShow={() => show([...A.dark, inc], ['night'])} />
      </div>
      <div className="sect">Assessment</div>
      <div className="row" style={{ marginBottom: 8 }}><Dmg d={inc.damage_class} /></div>
      <div className="row"><Ev e={inc.evidence} />{inc.second_sensor_agrees ? <span className="chip ev-Corroborated">Second sensor agrees</span> : <span className="tag">No second-sensor agreement</span>}</div>
      <div className="kpis" style={{ marginTop: 8 }}>
        <div className="kpi"><span className="k">Buildings</span><b>{inc.buildings_available === false ? 'Unknown' : rng(inc.buildings_candidate)}</b><span className="s">{inc.buildings_available === false ? 'Radar evidence unavailable' : 'Candidate damage'}</span></div>
        <div className="kpi"><span className="k">Score</span><b>{inc.score.low.toFixed(2)}–{inc.score.high.toFixed(2)}</b><span className="s">Ranking range</span></div>
      </div>
      <div style={{ marginTop: 8 }}><Note><b style={{ color: 'var(--ink)' }}>Check before acting.</b> Seen {p.date} ({p.sensor}), changes from {addHours(p.date, 72)}. Candidates only.</Note></div>
    </>
  } else if (tab === 'impacts') {
    const Row = ({ icon, t, children }: { icon: IconName; t: string; children: ReactNode }) => <div className="irow"><span className="ico"><Icon name={icon} size={16} /></span><div><div className="t">{t}</div><div className="m">{children}</div></div></div>
    const kind: Record<string, string> = { hospital: 'Hospital', clinic: 'Clinic', school: 'School', water: 'Water point', fuel: 'Fuel station' }
    body = <>
      <Row icon="people" t={inc.people_available === false ? 'People in the affected area: unknown' : `${rng(inc.people_nearby)} people in the affected area`}><Ev e={inc.people_available === false ? 'Unknown' : inc.evidence} /> {inc.people_available === false ? 'Population evidence unavailable' : 'WorldPop 2025 grid'}</Row>
      {A.facilities.length ? A.facilities.map(x => <Row key={x.f.id} icon="facility" t={`${kind[x.f.kind] || x.f.kind}: ${x.f.name}`}><Ev e={x.hz[0].ev} /><HzTags hz={x.hz} /></Row>)
        : <Row icon="facility" t="No facilities inside or near hazard areas"><span className="muted">Within {fmtM(AREA_M)}</span></Row>}
      {A.roads.map(r => <Row key={r.id} icon="road" t={`${r.label}: possibly blocked (candidate)`}><Ev e="Observed" /><span className="tag warn">Candidate</span> damage candidates next to the road</Row>)}
      {A.fireNear.map(x => <Row key={x.f.id} icon="fire" t={`Fire within 375 m of ${x.cells.length} candidate building cell${x.cells.length === 1 ? '' : 's'} and ${x.fac.length} facilit${x.fac.length === 1 ? 'y' : 'ies'}`}><Ev e={x.f.evidence} /> {x.f.source} · {x.f.detected_at.slice(0, 10)}</Row>)}
      {A.budget && <Row icon="money" t={`Rebuild budget ${A.budget.low.toFixed(1)}–${A.budget.high.toFixed(1)} ${A.budget.unit}`}><span className="tag">Indicative, not a quote</span> {A.budget.assumptions.join(' · ')}</Row>}
    </>
  } else if (tab === 'shelters') {
    body = <>
      {A.shelters.length ? <ul className="list">{A.shelters.map(x => {
        const q = ctx.engine?.pathFor(x.s.id), st = q && pathStats(D, q, passIdx)
        return <li key={x.s.id} className="card">
          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
            <div><h3>{x.s.name}</h3><div className="small muted">{x.s.kind} · {st ? `${fmtM(st.len)} by ${q!.source === 'osm' ? 'road' : 'straight line'}` : fmtM(x.m)}</div></div>
            <button className="btn sm" onClick={() => ctx.openShelter(x.s.id)}><Icon name="pin" size={13} />Show</button></div>
          <div className="row" style={{ marginTop: 8 }}><span className="tag">Candidate shelter, not verified</span>
            {st?.touches ? <span className="tag warn">Route passes possibly blocked road</span> : <span className="tag">Route not verified</span>}
            {x.hz.length ? <HzTags hz={x.hz} /> : <span className="tag">No hazard within 300 m on this pass</span>}</div>
          <dl className="kv" style={{ marginTop: 8 }}><dt>Capacity</dt><dd>{rng(x.s.capacity)} people (from floor area)</dd>
            <dt>Location</dt><dd>{x.s.lat.toFixed(5)}, {x.s.lon.toFixed(5)} <Copy text={`${x.s.lat.toFixed(5)}, ${x.s.lon.toFixed(5)}`} /></dd></dl>
        </li>
      })}</ul> : <p className="empty">No candidate shelters found near this incident.</p>}
      <div style={{ marginTop: 10 }}><Note>Routes follow OpenStreetMap roads (OSRM) but are not checked on the ground. Red parts pass damage candidates. Confirm each site and the way there before sending anyone.</Note></div>
    </>
  } else if (tab === 'power') {
    body = <>
      {A.dark.length ? <ul className="list">{A.dark.map(n => {
        const fac = D.facilities.filter(f => dist(n, f) <= n.size_m / 2)
        return <li key={n.id} className="card">
          <div className="row" style={{ justifyContent: 'space-between' }}><h3>Dark cell {n.id.toUpperCase()}</h3><Ev e={n.sensors_agree ? 'Corroborated' : 'Observed'} /></div>
          <div className="row" style={{ marginTop: 8 }}><span className="tag pw">Possible power loss</span><span className="tag">{n.sensors_agree ? 'Two satellites agree' : 'One satellite only'}</span></div>
          <dl className="kv" style={{ marginTop: 8 }}><dt>Last lit night</dt><dd>{n.last_lit ?? 'Unknown'}</dd><dt>People</dt><dd>{n.people_available === false ? 'Unknown' : `${rng(n.people)} (WorldPop)`}</dd>
            <dt>Facilities</dt><dd>{fac.length ? fac.map(f => f.name).join(', ') : 'None in cell (OSM)'}</dd></dl></li>
      })}</ul> : <p className="empty">No dark cells near this incident on this pass.</p>}
      {A.dark.length > 0 && <div className="row" style={{ marginTop: 10 }}><button className="btn sm" onClick={() => show([...A.dark, inc], ['night'])}><Icon name="pin" size={13} />Show dark cells</button></div>}
      <div style={{ marginTop: 10 }}><Note>Night-light change from VIIRS Black Marble. Dimming can also come from cloud or moonlight; it is not proof of an outage.</Note></div>
    </>
  } else {
    body = <ul className="list">{inc.insights.map((x, i) => <li key={i} className="card"><p style={{ margin: '0 0 8px' }}>{x.text}</p><div className="row small"><Ev e={x.evidence} /><span className="muted">{x.source} · {x.source_date}</span></div></li>)}</ul>
  }
  return <>
    <Head kicker={`Rank ${inc.rank} · ${inc.area}`} title={inc.name} onClose={onClose} />
    <div className="ptabs" role="tablist">{tabs.map(([k, t, n]) => <button key={k} className="ptab" role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>{t}{n !== undefined && <span className="n">{n}</span>}</button>)}</div>
    <div className="db" style={{ paddingTop: 14 }}>{body}</div>
    <div className="df"><span style={{ flex: 1 }}>Run {D.meta.run_id}</span><button className="linkbtn" onClick={() => ctx.engine?.flyToIncident(inc)}>Fly here again <Icon name="chev" size={14} /></button></div>
  </>
}

function BuildingDetail({ ctx, b, back, onClose }: { ctx: MapCtx; b: BuildingInfo; back: () => void; onClose: () => void }) {
  const c = b.cell
  return <><Head kicker="Building detail · OSM" title={b.name} onClose={onClose} />
    <div className="db">
      <button className="linkbtn" onClick={() => { ctx.engine?.clearBuildingHighlight(); back() }}>← Back to incident</button>
      <div className="row" style={{ margin: '12px 0 14px' }}>{c ? <><Dmg d={c.damage_class} /><Ev e={c.evidence} /></> : <span className="muted small">No damage candidate on this building in this run</span>}</div>
      <dl className="kv">
        <dt>OSM id</dt><dd>{b.id}</dd><dt>Footprint</dt><dd>OSM building outline</dd><dt>Height</dt><dd>{b.height}</dd><dt>Floors</dt><dd>{b.floors}</dd>
        <dt>Use</dt><dd>{b.use}</dd><dt>Material</dt><dd>{b.material || 'not tagged (neutral tone shown)'}</dd><dt>Facility</dt><dd>{b.facility ? 'Yes' : 'No'}</dd>
        <dt>Residents</dt><dd>{b.residents}</dd><dt>Damage class</dt><dd>{c ? DMG_LABEL[c.damage_class] : '—'}</dd><dt>Evidence</dt><dd>{c ? c.evidence : '—'}</dd>
        <dt>Second sensor</dt><dd>{c ? (c.second_sensor ? 'Agrees' : 'Not yet / disagrees') : '—'}</dd><dt>Run id</dt><dd>{ctx.data.meta.run_id}</dd>
      </dl>
      <div style={{ marginTop: 16 }}><Note>Shapes and heights come from OpenStreetMap. Damage values are sample data.</Note></div>
    </div></>
}

function ShelterDetail({ ctx, id, back, onClose }: { ctx: MapCtx; id: string; back: () => void; onClose: () => void }) {
  const D = ctx.data, sh = D.shelters.find(s => s.id === id)
  if (!sh) return null
  const inc = D.incidents.find(i => i.id === sh.incident_id)!
  const q = ctx.engine?.pathFor(id), st = q && pathStats(D, q, ctx.passIdx)
  const hz = analyse(D, inc, ctx.passIdx).hazardsAt(sh)
  const ll = `${sh.lat.toFixed(5)}, ${sh.lon.toFixed(5)}`, dm = `${dms(sh.lat, 'N', 'S')} ${dms(sh.lon, 'E', 'W')}`
  return <><Head kicker={`Candidate shelter · ${sh.kind}`} title={sh.name} onClose={onClose} />
    <div className="db" style={{ paddingTop: 8 }}>
      <button className="linkbtn" onClick={back}>← Back to {inc.name}</button>
      <div className="row" style={{ margin: '12px 0 4px' }}><span className="tag">Candidate shelter, not verified</span>{hz.length ? <HzTags hz={hz} /> : <span className="tag">No hazard within 300 m on this pass</span>}</div>
      <div className="sect">Location</div>
      <div className="locbox">
        <div className="locrow"><span className="muted">Decimal</span><b className="mono">{ll}</b><Copy text={ll} /></div>
        <div className="locrow"><span className="muted">DMS</span><b className="mono">{dm}</b><Copy text={dm} /></div>
        <div className="row" style={{ marginTop: 8 }}>
          <a className="btn sm" href={`https://www.openstreetmap.org/?mlat=${sh.lat}&mlon=${sh.lon}#map=18/${sh.lat}/${sh.lon}`} target="_blank" rel="noopener noreferrer">Open in OpenStreetMap ↗</a>
          <button className="btn sm" onClick={() => ctx.showOnMap([...(st ? st.pts : []), sh, inc], ['shelters'])}><Icon name="pin" size={13} />Show route on map</button></div>
      </div>
      <div className="sect">Getting there</div>
      <dl className="kv">
        <dt>From</dt><dd>{inc.name}</dd>
        <dt>Distance</dt><dd>{st ? `${fmtM(st.len)} by ${q!.source === 'osm' ? 'road' : 'straight line'}` : fmtM(dist(sh, inc))} ({fmtM(dist(sh, inc))} direct)</dd>
        <dt>Route</dt><dd style={{ color: st?.touches ? '#ff9a9d' : undefined }}>{st?.touches ? 'Passes a possibly blocked road (candidate)' : 'Not verified on the ground'}</dd>
        <dt>Capacity</dt><dd>{rng(sh.capacity)} people (from floor area)</dd><dt>Source</dt><dd>OSM {sh.kind} · capacity is sample</dd>
      </dl>
      <div style={{ marginTop: 12 }}><Note>Check the site is open, intact and reachable before sending anyone. The officer decides.</Note></div>
    </div></>
}

/* ---------- left drawers ---------- */
const LAYERS: [LayerKey, string, string][] = [
  ['damage', 'Damage candidates', 'Hatched volumes; never final damage'], ['second', 'Second-sensor ring', 'Dashed ring where a second satellite agrees'],
  ['change', 'NISAR change cells', 'Radar change, 120 m cells'], ['fires', 'Fires', 'Thermal points, 375 m uncertainty ring'],
  ['night', 'Night lights', 'Dark cells: possible power loss'], ['pop', 'Population (WorldPop)', 'People per cell, as a range'],
  ['facilities', 'Facilities', 'Hospitals, clinics, schools, water, fuel'], ['shelters', 'Candidate shelters', 'OSM sites, not verified'],
  ['routes', 'Routes', 'Not verified / possibly blocked (candidate)'], ['streets', 'Streets & labels', 'Road and place-name overlay'],
  ['buildings', '3D buildings (OSM)', 'Natural colours from material tags; 3D only'],
]

export function LeftPanel({ ctx, k, onClose }: { ctx: MapCtx; k: LeftKey | null; onClose: () => void }) {
  return <aside id="left" className={`drawer glass${k ? '' : ' hidden'}`} aria-label="Panel">{k && <LeftBody ctx={ctx} k={k} onClose={onClose} />}</aside>
}
function LeftBody({ ctx, k, onClose }: { ctx: MapCtx; k: LeftKey; onClose: () => void }) {
  const D = ctx.data, inc = ctx.selected
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [openWhy, setOpenWhy] = useState<string | null>(null)
  if (k.startsWith('page:')) {
    const page = k.slice(5)
    if (page === 'alerts') {
      const alerts = [
        ...D.fires.map(item => ({ id: item.id, title: 'Fire observation', detail: `${item.source} · ${item.detected_at.slice(0, 10)}`, point: item, evidence: item.evidence })),
        ...D.nightlights.map(item => ({ id: item.id, title: 'Possible power loss', detail: item.last_lit ? `Last lit ${item.last_lit}` : 'Last-lit date unavailable', point: item, evidence: item.sensors_agree ? 'Corroborated' as const : 'Observed' as const })),
      ]
      return <><Head kicker="Released observations" title="Alerts" onClose={onClose} /><div className="db">
        {alerts.length ? <ul className="list">{alerts.map(item => <li key={item.id} className="card"><div className="row"><b style={{ flex: 1 }}>{item.title}</b><Ev e={item.evidence} /></div><p className="small muted">{item.detail}</p><button className="btn sm" onClick={() => ctx.showOnMap([item.point])}><Icon name="pin" size={13} />Show</button></li>)}</ul> : <p className="empty">No released alerts are available for your scope.</p>}
      </div></>
    }
    if (page === 'areas') return <><Head kicker="Scoped incident areas" title="Areas" onClose={onClose} /><div className="db">
      {D.incidents.length ? <ul className="list">{D.incidents.map(item => <li key={item.id} className="card"><h3>{item.name}</h3><p className="small muted">{item.area} · rank {item.rank}</p><button className="btn sm" onClick={() => ctx.selectIncident(item.id, true)}><Icon name="pin" size={13} />Open incident</button></li>)}</ul> : <p className="empty">No released incident areas are available for your scope.</p>}
    </div></>
    const sources = [...new Set([...D.incidents.flatMap(item => item.insights.map(insight => insight.source)), ...D.fires.map(item => item.source)].filter(Boolean))]
    return <><Head kicker="Evidence provenance" title="Sources" onClose={onClose} /><div className="db">
      {sources.length ? <ul className="list">{sources.map(source => <li key={source} className="card"><h3>{source}</h3><p className="small muted">Referenced by a released observation. Open its incident for date and evidence context.</p></li>)}</ul> : <p className="empty">No released source records are available for this view.</p>}
    </div></>
  }
  if (k === 'rank') {
    const list = D.incidents.filter(i => passIndex(D, i.first_pass) <= ctx.passIdx).sort((a, b) => a.rank - b.rank)
    return <><Head kicker="Agent output · suggests only" title="Incident ranking" onClose={onClose} />
      <div className="db"><ol className="list">{list.map(i => <li key={i.id} className={`card${i.id === inc?.id ? ' sel' : ''}${openWhy === i.id ? ' open' : ''}`}>
        <div className="rankrow" role="button" tabIndex={0} onClick={() => ctx.selectIncident(i.id, true)} onKeyDown={e => { if (e.key === 'Enter') ctx.selectIncident(i.id, true) }}>
          <span className="rk" style={{ ['--c' as string]: `var(--dmg-${i.damage_class})` }}>{i.rank}</span>
          <div style={{ flex: 1, minWidth: 0 }}><h3>{i.name}</h3><div className="small muted">{i.area}</div>
            <div className="scorebar"><i style={{ left: `${i.score.low * 100}%`, width: `${(i.score.high - i.score.low) * 100}%` }} /></div>
            <div className="row small"><span className="mono">{i.score.low.toFixed(2)}–{i.score.high.toFixed(2)}</span><span className="muted">score</span><span style={{ flex: 1 }} /><Ev e={i.evidence} /></div></div></div>
        <div style={{ marginTop: 8, paddingLeft: 38 }}><button className="linkbtn" aria-expanded={openWhy === i.id} onClick={() => setOpenWhy(openWhy === i.id ? null : i.id)}>Why ranked here <Icon name="chev" size={14} /></button></div>
        <div className="why">{i.why.map(w => <div key={w.factor}><span>{w.factor}<br /><span className="muted">{w.value}</span></span><span className="mono muted">{Math.round(w.weight * 100)}%</span><span className="w"><i style={{ width: `${Math.min(100, (w.weight / 0.35) * 100)}%` }} /></span></div>)}</div>
      </li>)}</ol></div>
      <div className="df">Ranking is a suggestion. The officer decides what to act on.</div></>
  }
  if (k === 'decide') {
    if (!inc) return <><Head kicker="Agent output · suggests only" title="Decision assistant" onClose={onClose} /><div className="db"><p className="empty">Select an incident first.</p></div></>
    const A = analyse(D, inc, ctx.passIdx)
    const all = inc.suggestions.filter(s => !dismissed.has(s.id)), open = all.filter(s => !checked.has(s.id)), done = all.filter(s => checked.has(s.id))
    const routes = D.routes.filter(r => r.incident_id === inc.id).map(r => {
      const path = ctx.engine?.pathById(r.id), st = path ? pathStats(D, path, ctx.passIdx) : null
      const pts = st ? st.pts : r.coords.map(([lon, lat]) => ({ lon, lat }))
      const len = pts.slice(1).reduce((a, q, i) => a + dist(pts[i], q), 0)
      const nearDmg = A.cells.length ? Math.min(...A.cells.map(c => Math.min(...pts.map(q => Math.max(0, dist(c, q) - c.size_m / 2))))) : NaN
      const nearFire = A.fires.length ? Math.min(...A.fires.map(f => Math.min(...pts.map(q => dist(f, q))))) : NaN
      return { r, pts, len, nearDmg, nearFire, bl: r.status === 'possibly_blocked_candidate' }
    })
    const firstP = D.passes[passIndex(D, inc.first_pass)], missed = D.passes.slice(0, ctx.passIdx + 1).filter(x => x.status === 'missed')
    const gaps: [string, Evidence][] = [
      ...(!inc.second_sensor_agrees ? [['A second satellite has not confirmed this change yet.', 'Unknown'] as [string, Evidence]] : []),
      ...(missed.length ? [[`Missed pass on ${missed.map(x => x.date).join(', ')}: changes in between may be missing.`, 'Unknown'] as [string, Evidence]] : []),
      ['No field report from the ground yet for this incident.', 'Unknown'],
      [`Building changes from the ${firstP.date} pass appear from ${addHours(firstP.date, 72)}.`, 'Observed'],
    ]
    const ok = routes.filter(x => !x.bl).length, bl = routes.filter(x => x.bl).length
    const Sug = ({ s, isDone }: { s: typeof all[number]; isDone: boolean }) => <li className={`card sug${isDone ? ' done' : ''}`}>
      <div className="sug-top"><span className="sico"><Icon name={s.kind === 'route' ? 'road' : 'info'} size={14} /></span><span className="sug-t">{s.text}</span>
        <span className="sug-act">{!isDone && <button className="x sm" title="Mark as checked" aria-label="Mark as checked" onClick={() => setChecked(new Set(checked).add(s.id))}><Icon name="check" size={14} /></button>}
          <button className="x sm" title="Dismiss" aria-label="Dismiss suggestion" onClick={() => setDismissed(new Set(dismissed).add(s.id))}><Icon name="close" size={14} /></button></span></div>
      <div className="sug-why">{s.reason}</div>
      <div className="row" style={{ marginTop: 6, paddingLeft: 30 }}><span className="tag">{isDone ? 'Checked by officer' : 'Unverified'}</span><span className="tag">{s.kind === 'route' ? 'Route idea' : 'Field check'}</span></div></li>
    return <><Head kicker="Agent output · suggests only" title="Decision assistant" onClose={onClose} />
      <div className="db">
        <div className="dsum"><div><b>{open.length}</b><span>open checks</span></div><div><b>{ok}</b><span>route{ok === 1 ? '' : 's'} to check</span></div>
          <div><b style={{ color: '#ff9a9d' }}>{bl}</b><span>possibly blocked</span></div><div><b>{A.shelters.length}</b><span>shelter sites</span></div></div>
        <div className="row small muted" style={{ marginTop: 8 }}>For <b style={{ color: 'var(--ink)' }}>{inc.name}</b> · pass {D.passes[ctx.passIdx].date} <Ev e={inc.evidence} /></div>
        <div className="sect">Suggested next checks</div>
        {open.length ? <ul className="list">{open.map(s => <Sug key={s.id} s={s} isDone={false} />)}</ul> : <p className="empty">No open suggestions.</p>}
        {done.length > 0 && <ul className="list" style={{ marginTop: 6 }}>{done.map(s => <Sug key={s.id} s={s} isDone />)}</ul>}
        <div className="sect">Route options</div>
        <ul className="list">{routes.map(x => <li key={x.r.id} className={`card rcard${x.bl ? ' bl' : ''}`}>
          <div className="rt" style={{ border: 0, padding: 0 }}><svg width="22" height="10"><path d="M1 5h20" stroke={x.bl ? '#ff5a5f' : '#f1f4f3'} strokeWidth="3.5" strokeDasharray={x.bl ? '5 3' : undefined} /></svg>
            <b>{x.r.label}</b><KBtn label={`Show ${x.r.label} on map`} onClick={() => ctx.showOnMap(x.pts, ['routes'])} /></div>
          <div className="rmeta"><span><i>Length</i>{fmtM(x.len)}</span><span><i>Nearest damage</i>{isFinite(x.nearDmg) ? fmtM(x.nearDmg) : '—'}</span><span><i>Nearest fire</i>{isFinite(x.nearFire) ? fmtM(x.nearFire) : '—'}</span></div>
          <div className="row" style={{ marginTop: 6 }}><span className={`tag${x.bl ? ' warn' : ''}`}>{x.bl ? 'Possibly blocked (candidate)' : 'Available · not verified'}</span>{x.nearFire <= 375 && <span className="tag fire">Inside fire ring</span>}</div></li>)}</ul>
        <div className="sect">Shelters to consider</div>
        {A.shelters.length ? <><div className="card" style={{ padding: '2px 11px' }}>{A.shelters.slice(0, 3).map(x => <div key={x.s.id} className="rt"><span className="sico"><Icon name="shelter" size={14} /></span>
          <span style={{ flex: 1, minWidth: 0 }}><b style={{ display: 'block' }}>{x.s.name}</b><span className="muted" style={{ fontSize: 11.5 }}>{fmtM(x.m)} · {rng(x.s.capacity)} people{x.hz.length ? ' · near hazard' : ''}</span></span>
          <KBtn label="Show shelter" onClick={() => ctx.openShelter(x.s.id)} /></div>)}</div><p className="small muted" style={{ margin: '6px 0 0' }}>Candidate shelters, not verified.</p></>
          : <p className="empty">No candidate shelters nearby.</p>}
        <div className="sect">Data gaps</div>
        <ul className="gaps">{gaps.map(([t, e]) => <li key={t}><span className={`gdot ev-${e}`} />{t}</li>)}</ul>
      </div>
      <div className="df">Suggestions only. The officer chooses the route.</div></>
  }
  if (k === 'budget') {
    const max = Math.max(...D.budget.map(b => b.high))
    return <><Head kicker="Agent output · indicative" title="Rebuild budget" onClose={onClose} />
      <div className="db"><ul className="list">{D.budget.map(b => <li key={b.area} className="card"><h3>{b.area}</h3>
        <div className="budget-bar"><i style={{ left: `${(b.low / max) * 100}%`, width: `${((b.high - b.low) / max) * 100}%` }} /></div>
        <div className="mono" style={{ fontSize: 16, fontWeight: 600 }}>{b.low.toFixed(1)}–{b.high.toFixed(1)} <span className="muted" style={{ fontSize: 12, fontWeight: 400 }}>{b.unit}</span></div>
        <div className="sect" style={{ margin: '12px 0 6px' }}>Assumptions</div>
        <ul className="small" style={{ margin: 0, paddingLeft: 18, color: 'var(--ink-2)' }}>{b.assumptions.map(a => <li key={a}>{a}</li>)}</ul></li>)}</ul></div>
      <div className="df"><b style={{ color: 'var(--ink-2)' }}>Indicative, not a quote.</b> Ranges from sample data.</div></>
  }
  // layers
  return <><Head kicker="Map" title="Layers" onClose={onClose} />
    <div className="db">{LAYERS.map(([key, t, d]) => <div key={key} className="toggle"><label htmlFor={`ly-${key}`}>{t}<small>{d}</small></label>
      <span className="switch"><input type="checkbox" id={`ly-${key}`} checked={ctx.layers[key]} onChange={e => ctx.setLayer(key, e.target.checked)} /><i /></span></div>)}
      <div style={{ marginTop: 16 }}><Note>Layers are shared by the 2D and 3D views. Damage overlays sit on top of buildings and never change their material colours.</Note></div></div></>
}
