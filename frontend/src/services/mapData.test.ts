import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api'
import { toMapData, type FrontendMapBundle } from './mapData'

const bundle: FrontendMapBundle = {
  synthetic: false,
  generated_at: '2026-11-15T00:00:00Z',
  incidents: { items: [{
    incident_id: 'i1', area_id: 'area-1', kind: 'damage_candidate_area', rank: 1, score_low: 20, score_high: 40,
    parts: { people: { status: 'known', value: 25, points: 10, weight: 30, detail: '25 people (modelled range)' } },
    reasons: ['Candidate surface change'], unknowns: ['No field verification'],
  }] },
  incident_details: { i1: {
    incident: {} as never,
    insights: [{ text: 'One reviewed candidate.', sources: ['nisar'], date: '2026-11-14' }],
    recommendation: { checklist: ['Verify on the ground'] },
  } },
  layers: { items: [{ layer_id: 'nisar-change', product: 'NISAR', available_acquisitions: ['2026-11-14T10:00:00Z'], missing_intervals: [] }] },
  damage: { 'area-1': { items: [{ area_id: 'cell-1', candidate_class: 'moderate_candidate', score: 0.5, reason_codes: [], run_id: 'run-1' }] } },
  alerts: { items: [] },
  people: { 'area-1': { items: [{ metric: 'potentially_affected_people', low: 20, high: 30, label: 'Unknown', date: '2026-11-14', source: ['worldpop'] }] } },
  budgets: {},
  centroids: { 'area-1': [33.3, 35.5], 'cell-1': [33.301, 35.501] },
  unavailable: { shelters: 'Validated shelter data is not loaded.' },
}

afterEach(() => vi.unstubAllGlobals())

it('maps released API evidence without filling unavailable domains', () => {
  const data = toMapData(bundle)
  expect(data.passes).toEqual([{ id: '2026-11-14', date: '2026-11-14', sensor: 'NISAR', status: 'ok' }])
  expect(data.incidents[0]).toMatchObject({ id: 'i1', evidence: 'Unknown', people_nearby: { low: 20, high: 30 } })
  expect(data.damage_cells[0]).toMatchObject({ id: 'cell-1', damage_class: 'moderate', evidence: 'Unknown' })
  expect(data.shelters).toEqual([])
  expect(data.meta.availability).toEqual(bundle.unavailable)
})

it('preserves missing acquisitions and unavailable raster layers', () => {
  const missing = structuredClone(bundle)
  missing.layers.items[0].available_acquisitions = ['2026-11-14T10:00:00Z']
  missing.layers.items[0].missing_intervals = [{ start: '2026-11-26T00:00:00Z', end: '2026-11-27T00:00:00Z', reason: 'No released pass' }]
  missing.layers.items[0].tile_url = undefined
  const data = toMapData(missing)
  expect(data.passes).toEqual([
    { id: '2026-11-14', date: '2026-11-14', sensor: 'NISAR', status: 'ok' },
    { id: 'missed-2026-11-26', date: '2026-11-26', sensor: 'No released pass', status: 'missed' },
  ])
  expect(data.radar_layers).toEqual([])
})

it('uses the backend bundle when the API serves it', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => bundle })
  vi.stubGlobal('fetch', fetchMock)
  const result = await api.mapData()
  expect(result.sample).toBe(false)
  expect(fetchMock).toHaveBeenCalledWith('/api/v1/map/context?limit=100', expect.objectContaining({ credentials: 'include' }))
})

it('falls back to the labelled sample file when the API is unavailable', async () => {
  const sample = toMapData(bundle)
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: false, json: async () => ({ error: { code: 'UNAVAILABLE', message: 'no backend', request_id: 't', details: [] }, synthetic: true }) })
    .mockResolvedValueOnce({ ok: true, json: async () => sample })
  vi.stubGlobal('fetch', fetchMock)
  const result = await api.mapData()
  expect(result.sample).toBe(true)
  expect(fetchMock).toHaveBeenLastCalledWith('/sample/civisar-3d-sample.json', { cache: 'no-store' })
})
