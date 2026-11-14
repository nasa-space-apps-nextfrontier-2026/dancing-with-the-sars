import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AreaExplorer } from '../area/AreaExplorer'

type Panel = 'agents' | 'layers' | 'alerts' | 'time' | 'legend'
const dock: { id: Panel; label: string; symbol: string }[] = [
  { id: 'layers', label: 'Layers', symbol: '▤' },
  { id: 'agents', label: 'Agents', symbol: '▦' },
  { id: 'alerts', label: 'Alerts', symbol: '♢' },
  { id: 'time', label: 'Time', symbol: '◷' },
  { id: 'legend', label: 'Legend', symbol: '≡' },
]

export function PrototypeMain() {
  const [panels, setPanels] = useState<Panel[]>(['agents', 'time'])
  const [alertFilter, setAlertFilter] = useState('All')
  function toggle(id: Panel) {
    setPanels(previous => previous.includes(id) ? previous.filter(x => x !== id) : [...previous, id])
  }
  return <section id="v-main" className="prototype-main" aria-label="NISAR change workspace">
    <h1 className="sr-only">NISAR change workspace</h1>
    <div className="cv-map prototype-map">
      <div className="cv-demo">ILLUSTRATIVE DEMO DATA · NOT AN ASSESSMENT</div>
      <div className="dock" aria-label="Map panels">{dock.map(item => <button key={item.id}
        aria-pressed={panels.includes(item.id)} className={panels.includes(item.id) ? 'is-on' : ''}
        onClick={() => toggle(item.id)}><span aria-hidden="true">{item.symbol}</span>{item.label}</button>)}</div>
      <AreaExplorer />
      {panels.includes('agents') && <aside className="ov prototype-agents" aria-label="AI agent results">
        <div className="ov-h"><span className="cv-row"><b>AI agent results</b><span className="cv-count">Unknown</span></span><button className="cv-btn cv-btn--ghost cv-btn--sm" onClick={() => toggle('agents')}>Close</button></div>
        <div className="cv-xs cv-faint cv-pad">No validated agent results loaded.</div>
        {['Damage', 'Facilities', 'Services lost', 'People affected', 'Hazards', 'Routes', 'Shelters', 'Movement'].map(name => <div className="ag" key={name}><div className="ag-h"><div className="cv-grow"><b>{name}</b><div className="cv-xs cv-muted">Unavailable · awaiting reviewed evidence</div></div><span className="cv-ev cv-ev--unk">Unknown</span></div></div>)}
      </aside>}
      {panels.includes('layers') && <aside className="ov prototype-layers" aria-label="Layers">
        <div className="ov-h"><b>Layers</b><button className="cv-btn cv-btn--ghost cv-btn--sm" onClick={() => toggle('layers')}>Close</button></div>
        <div className="cv-layer-group"><span className="cv-eyebrow">Data layers</span><span className="cv-xs cv-faint">NASA first</span></div>
        <div className="cv-layer is-on"><span className="cv-sw is-on"/><span className="cv-swatch" style={{background:'var(--radar)'}}/>Synthetic NISAR comparison <span className="cv-tag">CORE</span></div>
        <p className="cv-pad cv-sm">Other prototype layers need reviewed sources and authorization.</p>
      </aside>}
      {panels.includes('alerts') && <aside className="ov prototype-alerts" aria-label="Alerts">
        <div className="ov-h"><b>Alerts</b><button className="cv-btn cv-btn--ghost cv-btn--sm" onClick={() => toggle('alerts')}>Close</button></div>
        <div className="cv-row cv-pad">{['All','Fire','Power','Internet','Radar','Reports'].map(filter => <button key={filter} className={`cv-tag ${alertFilter === filter ? 'is-on' : ''}`} onClick={() => setAlertFilter(filter)}>{filter}</button>)}</div>
        <div className="cv-banner cv-banner--off">No verified {alertFilter.toLowerCase()} alerts loaded.</div>
      </aside>}
      {panels.includes('legend') && <aside className="ov prototype-legend" aria-label="Legend"><div className="ov-h"><b>Legend</b><button className="cv-btn cv-btn--ghost cv-btn--sm" onClick={() => toggle('legend')}>Close</button></div><div className="cv-legend"><span className="cv-eyebrow">NISAR comparison</span><span>Synthetic illustration · Unknown evidence</span><span>No damage classification</span></div></aside>}
      <div className="pill prototype-pill"><b>Alerts unavailable</b><span className="cv-muted cv-sm">· No reviewed live feed</span><button className="cv-btn cv-btn--sm" onClick={() => toggle('alerts')}>Open</button></div>
      <div className="cv-mapctl prototype-zoom"><div className="cv-mapbox cv-zoom"><span>+</span><span>−</span></div></div>
      <div className="cv-attrib">Synthetic grid · no geolocation or satellite imagery</div>
      <Link className="cv-btn prototype-inspect" to="/inspector">Inspector</Link>
    </div>
  </section>
}
