import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { MapData } from '../../types/map'

vi.mock('./engine', () => ({ DMG_LABEL: { destroyed: 'Destroyed', severe: 'Severe', moderate: 'Moderate', possible: 'Possible' } }))

import type { MapCtx } from './MapScreen'
import { LeftPanel } from './panels'

const data: MapData = {
  meta: { run_id: 'run-1', generated_at: '2026-01-01', region: 'Test', change_delay_hours: 72, officer: 'Test' },
  imagery: { with_token: '', without_token: '' },
  passes: [{ id: 'p1', date: '2026-01-01', sensor: 'NISAR', status: 'ok' }],
  incidents: [{ id: 'i1', name: 'Incident One', area: 'area-1', lat: 1, lon: 2, rank: 1, score: { low: 0.2, high: 0.4 }, damage_class: 'possible', evidence: 'Unknown', second_sensor_agrees: false, first_pass: 'p1', buildings_candidate: { low: 0, high: 0 }, people_nearby: { low: 0, high: 0 }, why: [], insights: [], suggestions: [] }],
  damage_cells: [], change_cells: [], fires: [], nightlights: [], population: [], facilities: [], shelters: [], routes: [], budget: [],
}

afterEach(cleanup)

it('opens an incident from both the Areas and ranking controls', () => {
  const selectIncident = vi.fn()
  const ctx = { data, passIdx: 0, layers: {}, selected: null, engine: null, roadsVersion: 0, sources: { status: 'ready', items: [], error: '' }, selectIncident } as unknown as MapCtx
  const view = render(<LeftPanel ctx={ctx} k="page:areas" onClose={() => {}} />)
  fireEvent.click(screen.getByRole('button', { name: 'Open incident' }))
  expect(selectIncident).toHaveBeenLastCalledWith('i1', true)
  view.rerender(<LeftPanel ctx={ctx} k="rank" onClose={() => {}} />)
  fireEvent.click(screen.getByText('Incident One'))
  expect(selectIncident).toHaveBeenLastCalledWith('i1', true)
})
