import area from '../../../docs/contracts/AreaSummary.json'
import alert from '../../../docs/contracts/AlertDetail.json'
import layer from '../../../docs/contracts/Layer.json'
import route from '../../../docs/contracts/RouteOption.json'
import shelter from '../../../docs/contracts/ShelterCandidate.json'
import source from '../../../docs/contracts/SourceRecord.json'
import value from '../../../docs/contracts/MetricValue.json'

// These types are derived from the canonical JSON fixtures. H2 generated types will replace them.
export type AreaSummary = typeof area
export type AlertDetail = typeof alert
export type Layer = typeof layer
export type RouteOption = typeof route
export type ShelterCandidate = typeof shelter
export type SourceRecord = typeof source
export type MetricValue = typeof value
export type RadarObservation = {
  observation_id: string
  source_id: string
  acquired_at: string
  processing_version: string
  product_maturity: 'beta' | 'provisional' | 'validated'
  polarizations: string[]
  raster_crs: string
  valid_pixel_count: number
  raster_available: boolean
  qa_status: string
  evidence_label: 'Observed' | 'Estimated' | 'Unknown'
  limitations: string[]
}
export type MissingInterval = { start: string; end: string; reason: string }
export type RadarSeries = {
  synthetic: boolean
  layer_id: string
  area_id: string
  track: number
  frame: number
  orbit: string
  points: RadarObservation[]
  missing_intervals: MissingInterval[]
}
export type LayerList = { synthetic: boolean; items: Layer[]; next_cursor: string | null }
export const fixtures = { area, alert, layer, route, shelter, source, value }
