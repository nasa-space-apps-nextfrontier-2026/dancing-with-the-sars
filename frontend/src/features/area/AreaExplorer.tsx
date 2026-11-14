import { useState } from 'react'
import { DataAge, EvidenceLabel, SystemState } from '../../components/Evidence'
import { MapPanel } from '../../components/MapPanel'
import { api } from '../../services/api'
import type { AreaSummary, SourceRecord } from '../../types/contracts'
import './AreaExplorer.css'

const DEMO_AREA_ID = 'demo-area-01'
type LoadState =
  | { status: 'idle' | 'loading' | 'error' }
  | { status: 'ready'; area: AreaSummary; source: SourceRecord }

export function AreaExplorer() {
  const [state, setState] = useState<LoadState>({ status: 'idle' })

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
    } catch {
      setState({ status: 'error' })
    }
  }

  const ready = state.status === 'ready' ? state : null
  const residents = ready?.area.people.residents
  const range = residents?.low == null || residents.high == null
    ? 'Unknown' : `${residents.low.toLocaleString()}–${residents.high.toLocaleString()} ${residents.unit}`

  return <div className="area-explorer">
    <MapPanel onSelectDemoArea={selectDemoArea}/>
    <p className="map-note">The demo-area control has no geographic location. The map contains no NISAR image or operational point.</p>
    {state.status === 'idle' && <SystemState kind="empty" message="Select the synthetic demo area to request its area summary from the API."/>}
    {state.status === 'loading' && <SystemState kind="loading" message="Loading synthetic area and source from the API…"/>}
    {state.status === 'error' && <SystemState kind="error" message="Area information is unavailable. Check sign-in and the local API."/>}
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
