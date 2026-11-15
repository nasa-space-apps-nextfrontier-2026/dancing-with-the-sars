import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { MapData } from '../../types/map'

vi.mock('./engine', () => ({ DMG_LABEL: { destroyed: 'Destroyed', severe: 'Severe', moderate: 'Moderate', possible: 'Possible' } }))

import type { MapCtx } from './MapScreen'
import { LeftPanel, RightPanel } from './panels'

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

it('real data: missing facility, road and night-light inputs read Unknown, never zero', () => {
  const real = { ...data, meta: { ...data.meta, availability: {
    facilities: 'Facilities are listed per area, not on this map.',
    routes: 'Validated road and closure data is not loaded.',
    night_lights: 'Night-light history is not loaded: possible power loss is Unknown, not zero.',
  } } }
  const ctx = { data: real, passIdx: 0, layers: {}, selected: real.incidents[0], engine: null, roadsVersion: 0, sources: { status: 'ready', items: [], error: '' }, selectIncident: vi.fn(), showOnMap: vi.fn() } as unknown as MapCtx
  render(<RightPanel ctx={ctx} open view={{ kind: 'incident' }} setView={() => {}} onClose={() => {}} />)
  expect(screen.getAllByText('Unknown').length).toBeGreaterThanOrEqual(3)
  expect(screen.getByText('Facilities are listed per area, not on this map.')).toBeTruthy()
  expect(screen.getByText('Road data is not loaded')).toBeTruthy()
  expect(screen.queryByText('No dark cells on this pass')).toBeNull()
})

it('sample data keeps its counts', () => {
  const ctx = { data, passIdx: 0, layers: {}, selected: data.incidents[0], engine: null, roadsVersion: 0, sources: { status: 'ready', items: [], error: '' }, selectIncident: vi.fn(), showOnMap: vi.fn() } as unknown as MapCtx
  render(<RightPanel ctx={ctx} open view={{ kind: 'incident' }} setView={() => {}} onClose={() => {}} />)
  expect(screen.getByText('No dark cells on this pass')).toBeTruthy()
  expect(screen.getByText('Possibly blocked (candidate)')).toBeTruthy()
})
