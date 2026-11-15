import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { SourceRecord } from '../../services/api'
import { SourcesPanel } from './SourcesPanel'

const source: SourceRecord = {
  synthetic: false,
  source_id: 'nisar-1',
  dataset_id: 'DS01',
  name: 'Reviewed radar catalogue',
  provider: 'Provider',
  product_level: 'L2',
  cmr_concept_id: 'C1',
  challenge_provenance: 'Resources tab',
  source_url: 'https://example.test/source',
  acquisition_start: '2026-01-19T00:00:00Z',
  acquisition_end: '2026-01-19T00:00:00Z',
  processing_version: '1.0',
  spatial_coverage: { area_id: 'area-1', geometry: null, track: 151, frame: 72 },
  resolution_m: null,
  licence: 'Review required',
  accessed_at: null,
  api: 'Catalogue API',
  checksum: null,
  independence_family: 'radar',
  live_tested: false,
  limits: ['No empirical validation completed.'],
}

afterEach(cleanup)

it('shows catalogue loading, empty and error states', () => {
  const close = vi.fn()
  const view = render(<SourcesPanel catalogue={{ status: 'loading', items: [], error: '' }} onClose={close} />)
  expect(screen.getByRole('status').textContent).toContain('Loading')
  view.rerender(<SourcesPanel catalogue={{ status: 'ready', items: [], error: '' }} onClose={close} />)
  expect(screen.getByText('No approved source records are available.')).toBeTruthy()
  view.rerender(<SourcesPanel catalogue={{ status: 'error', items: [], error: 'Catalogue unavailable.' }} onClose={close} />)
  expect(screen.getByRole('alert').textContent).toContain('Catalogue unavailable.')
})

it('renders source provenance, maturity, dates and limitations', () => {
  render(<SourcesPanel catalogue={{ status: 'ready', items: [source], error: '' }} onClose={() => {}} />)
  expect(screen.getByRole('heading', { name: source.name })).toBeTruthy()
  expect(screen.getByText('Not live-tested')).toBeTruthy()
  expect(screen.getByText(source.acquisition_start)).toBeTruthy()
  expect(screen.getByText(source.licence)).toBeTruthy()
  expect(screen.getByText(source.limits[0])).toBeTruthy()
  expect(screen.getByRole('link', { name: 'Open provider record' }).getAttribute('href')).toBe(source.source_url)
})

it('does not expose a non-HTTP catalogue URL as a link', () => {
  render(<SourcesPanel catalogue={{ status: 'ready', items: [{ ...source, source_url: 'javascript:alert(1)' }], error: '' }} onClose={() => {}} />)
  expect(screen.queryByRole('link', { name: 'Open provider record' })).toBeNull()
})
