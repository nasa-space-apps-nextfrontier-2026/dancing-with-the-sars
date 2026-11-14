import { useState } from 'react'
import { DataAge, EvidenceLabel, SystemState } from '../../components/Evidence'
import { MapPanel, type RadarMode, type Polarization, type RadarView } from '../../components/MapPanel'
import { api, apiErrorCode } from '../../services/api'
import type { AreaSummary, SourceRecord } from '../../types/contracts'
import './AreaExplorer.css'

const DEMO_AREA_ID = 'demo-area-01'
type LoadState =
  | { status: 'idle' | 'loading' | 'error' | 'denied' }
  | { status: 'ready'; area: AreaSummary; source: SourceRecord }

export function AreaExplorer() {
  const [state, setState] = useState<LoadState>({ status: 'idle' })
  const [view, setView] = useState<RadarView>({ mode: 'before', polarization: 'HH', opacity: 75, split: 50 })
  const [scene, setScene] = useState(0)

  async function selectDemoArea() {
    setState({ status: 'loading' })
    try {
      const area = await api.areaSummary(DEMO_AREA_ID)
      if (area.synthetic !== true || area.area_id !== DEMO_AREA_ID) throw new Error('Unexpected area')
      const sourceId = area.people.residents.source[0]
      if (!sourceId) throw new Error('Missing source')
      const source = await api.sourceRecord(sourceId)
      if (source.synthetic !== true || source.source_id !== sourceId) throw new Error('Unexpected source')
      setState({ status: 'ready', area, source })
    } catch (failure) {
      setState({ status: apiErrorCode(failure) === 'FORBIDDEN' ? 'denied' : 'error' })
    }
  }

  const ready = state.status === 'ready' ? state : null
  const residents = ready?.area.people.residents
  const range = residents?.low == null || residents.high == null
    ? 'Unknown' : `${residents.low.toLocaleString()}–${residents.high.toLocaleString()} ${residents.unit}`

  return <div className="area-explorer">
    <div className="radar-controls" aria-label="Synthetic radar comparison controls">
      <fieldset><legend>View</legend>{(['before','after','change','swipe'] as RadarMode[]).map(mode =>
        <button key={mode} type="button" aria-pressed={view.mode === mode} onClick={() => {setView({...view,mode});if(mode==='before'||mode==='after')setScene(mode==='before'?0:1)}}>{mode[0].toUpperCase()+mode.slice(1)}</button>)}</fieldset>
      <fieldset><legend>Polarization</legend>{(['HH','HV','HH-HV'] as Polarization[]).map(polarization =>
        <button key={polarization} type="button" aria-pressed={view.polarization === polarization} onClick={() => setView({...view,polarization})}>{polarization}</button>)}</fieldset>
      <label>Acquisition window endpoint <input type="range" min="0" max="1" step="1" value={scene} onChange={event => {const next=Number(event.target.value);setScene(next);setView({...view,mode:next===0?'before':'after'})}}/></label>
      <output>{scene === 0 ? 'Before window: 27 Oct 2025–19 Jan 2026' : 'After window: 24 Jun–03 Nov 2026'}</output>
      {view.mode === 'swipe' && <label>Swipe split {view.split}%<input type="range" min="0" max="100" step="1" value={view.split} onChange={event => setView({...view,split:Number(event.target.value)})}/></label>}
      <label>Layer opacity {view.opacity}%<input type="range" min="0" max="100" step="5" value={view.opacity} onChange={event => setView({...view,opacity:Number(event.target.value)})}/></label>
    </div>
    <MapPanel onSelectDemoArea={selectDemoArea} radar={view}/>
    <p className="map-note">Synthetic non-georeferenced cells only. South Lebanon demo scope: track 151 descending, frame 72. Processing: synthetic-ui-v1. Provenance: PROJECT_PLAN.md snapshot of 13 Nov 2026; no granule IDs or validated radar pixels loaded. Evidence: Unknown. Uncertainty: unvalidated illustration. Acquisition gap: 20 Jan–17 Jun 2026; no observations are interpolated. Slider selects window endpoints, not individual passes.</p>
    {state.status === 'idle' && <SystemState kind="empty" message="Select the synthetic demo area to request its area summary from the API."/>}
    {state.status === 'loading' && <SystemState kind="loading" message="Loading synthetic area and source from the API…"/>}
    {state.status === 'error' && <SystemState kind="error" message="Area information is unavailable. Check sign-in and the local API."/>}
    {state.status === 'denied' && <SystemState kind="error" message="Access denied for this area. Your server-side role or area scope does not permit it."/>}
    {ready && <section className="area-result" aria-label="Selected area summary">
      <h3>{ready.area.name} <span className="demo-inline">Synthetic example</span></h3>
      <p>Residents (synthetic range): <strong>{range}</strong></p>
      <EvidenceLabel label={residents?.label ?? 'Unknown'}/>
      <DataAge freshness={ready.area.freshness} cached={ready.area.cached}/>
      <p>{ready.area.warning}</p>
      <p>Contract fixture source: <strong>{ready.source.name}</strong> · {ready.source.processing_version}. This example is not evidence for the synthetic resident range.</p>
      <p>Acquisition: {ready.source.acquisition_start}. Scientific validation: {ready.source.live_tested ? 'See source record' : 'Not performed for this fixture'}.</p>
      <p>{ready.source.limits.join(' ')}</p>
    </section>}
  </div>
}
