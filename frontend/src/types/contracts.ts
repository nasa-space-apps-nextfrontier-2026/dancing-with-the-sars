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
export const fixtures = { area, alert, layer, route, shelter, source, value }
