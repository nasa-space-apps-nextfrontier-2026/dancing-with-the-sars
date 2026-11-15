import type {
  Budget, DamageCell, Evidence, Fire, Incident, MapData, NightCell, Pass, PopCell, Range,
} from '../types/map'

type IncidentPart = { status: 'known' | 'unknown' | 'not_applicable'; value: number | null; points: number | null; weight: number; detail: string }
type ApiIncident = {
  incident_id: string; area_id: string; kind: 'fire_detected' | 'possible_power_loss' | 'damage_candidate_area'
  rank: number; score_low: number; score_high: number; parts: Record<string, IncidentPart>; reasons: string[]; unknowns: string[]
}
type ApiInsight = { text: string; sources: string[]; date: string | null }
type ApiRecommendation = { checklist: string[] }
type ApiIncidentDetail = { incident: ApiIncident; insights: ApiInsight[]; recommendation: ApiRecommendation }
type ApiDamage = { area_id: string; candidate_class: string; score: number | null; reason_codes: string[]; run_id: string }
type ApiLayer = { layer_id: string; title?: string; product: string; tile_url?: string; date?: string; attribution?: string; available_acquisitions: string[]; missing_intervals: { start: string; end: string; reason: string }[] }
type ApiMetric = { metric: string; low: number; high: number; label: Evidence; date: string; source: string[] }
type ApiAlert = {
  alert_id: string; area_id: string; type: 'fire_detected' | 'possible_power_loss'; detected_at: string; label: Evidence
  source: string[]; satellite: string; rings: { radius_m: number; people: ApiMetric }[]
}
type ApiBudget = { area_id: string; cost_usd: Range; assumptions: Record<string, unknown>; limits: string[] }

export type FrontendMapBundle = {
  synthetic: false
  generated_at: string
  incidents: { items: ApiIncident[] }
  incident_details: Record<string, ApiIncidentDetail>
  layers: { items: ApiLayer[] }
  damage: Record<string, { items: ApiDamage[] }>
  alerts: { items: ApiAlert[] }
  people: Record<string, { items: ApiMetric[] }>
  budgets: Record<string, ApiBudget>
  centroids: Record<string, [number, number]>
  unavailable: Record<string, string>
}

const range = (value: number | null | undefined): Range => {
  const n = value == null ? 0 : Math.max(0, Math.round(value))
  return { low: n, high: n }
}

function centre(bundle: FrontendMapBundle, areaId: string) {
  const point = bundle.centroids[areaId]
  return point ? { lat: point[0], lon: point[1] } : null
}

function damageClass(value: string | undefined): Incident['damage_class'] {
  if (value === 'destroyed_or_severe_candidate') return 'severe'
  if (value === 'moderate_candidate') return 'moderate'
  return 'possible'
}

function passes(bundle: FrontendMapBundle): Pass[] {
  const byDate = new Map<string, Pass>()
  for (const layer of bundle.layers.items) {
    for (const acquired of layer.available_acquisitions) {
      const date = acquired.slice(0, 10)
      if (!byDate.has(date)) byDate.set(date, { id: date, date, sensor: layer.product, status: 'ok' })
    }
    for (const gap of layer.missing_intervals) {
      const date = gap.start.slice(0, 10)
      if (!byDate.has(date)) byDate.set(date, { id: `missed-${date}`, date, sensor: gap.reason || layer.product, status: 'missed' })
    }
  }
  return [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date))
}

function affectedPeople(bundle: FrontendMapBundle, areaId: string): Range | undefined {
  const values = bundle.people[areaId]?.items ?? []
  const value = values.find(v => v.metric === 'potentially_affected_people') ?? values[0]
  return value ? { low: value.low, high: value.high } : undefined
}

/** Convert the authenticated API bundle into the unchanged 3D-map view model. */
export function toMapData(bundle: FrontendMapBundle): MapData {
  const timeline = passes(bundle)
  const latestPass = timeline.filter(pass => pass.status === 'ok').at(-1)?.id ?? ''
  const damageCells: DamageCell[] = []

  for (const incident of bundle.incidents.items) {
    for (const cell of bundle.damage[incident.area_id]?.items ?? []) {
      const point = centre(bundle, cell.area_id)
      if (!point) continue
      damageCells.push({
        id: cell.area_id,
        incident_id: incident.incident_id,
        ...point,
        size_m: 350,
        damage_class: damageClass(cell.candidate_class),
        evidence: 'Unknown',
        second_sensor: cell.reason_codes.some(reason => /second|sentinel/i.test(reason)),
        pass_id: latestPass,
      })
    }
  }

  const incidents: Incident[] = bundle.incidents.items.flatMap(item => {
    const point = centre(bundle, item.area_id)
    if (!point || !latestPass) return []
    const detail = bundle.incident_details[item.incident_id]
    const cells = damageCells.filter(cell => cell.incident_id === item.incident_id)
    const people = affectedPeople(bundle, item.area_id)
    const damageAvailable = !bundle.unavailable[`damage:${item.area_id}`]
    const suggestions = detail?.recommendation.checklist ?? []
    return [{
      id: item.incident_id,
      name: item.reasons[0] || item.kind.replaceAll('_', ' '),
      area: item.area_id,
      ...point,
      rank: item.rank,
      score: { low: item.score_low / 100, high: item.score_high / 100 },
      damage_class: cells[0]?.damage_class ?? 'possible',
      evidence: 'Unknown',
      second_sensor_agrees: cells.some(cell => cell.second_sensor),
      first_pass: latestPass,
      buildings_candidate: range(cells.length),
      buildings_available: damageAvailable,
      people_nearby: people ?? { low: 0, high: 0 },
      people_available: !!people,
      why: Object.entries(item.parts).map(([factor, part]) => ({ factor, value: part.detail, weight: part.weight / 100 })),
      insights: (detail?.insights ?? []).map(insight => ({ text: insight.text, evidence: 'Unknown' as Evidence, source: insight.sources.join(', '), source_date: insight.date ?? 'Unknown' })),
      suggestions: suggestions.map((text, index) => ({ id: `${item.incident_id}-check-${index + 1}`, kind: 'check' as const, text, reason: item.unknowns[index] ?? 'Requires officer verification.' })),
    }]
  })

  const fires: Fire[] = bundle.alerts.items.flatMap(alert => {
    if (alert.type !== 'fire_detected') return []
    const point = centre(bundle, alert.area_id)
    return point ? [{ id: alert.alert_id, ...point, detected_at: alert.detected_at, source: alert.source.join(', ') || alert.satellite, evidence: alert.label, uncertainty_m: Math.max(0, ...alert.rings.map(r => r.radius_m)), pass_id: latestPass }] : []
  })
  const nightlights: NightCell[] = bundle.alerts.items.flatMap(alert => {
    if (alert.type !== 'possible_power_loss') return []
    const point = centre(bundle, alert.area_id)
    const people = alert.rings[0]?.people
    return point ? [{ id: alert.alert_id, ...point, size_m: 900, state: 'dark', pass_id: latestPass, last_lit: null, sensors_agree: alert.label === 'Corroborated', people: people ? { low: people.low, high: people.high } : { low: 0, high: 0 }, people_available: !!people }] : []
  })
  const population: PopCell[] = Object.entries(bundle.people).flatMap(([areaId]) => {
    const point = centre(bundle, areaId)
    const people = affectedPeople(bundle, areaId)
    return point && people ? [{ id: areaId, ...point, size_m: 900, people }] : []
  })
  const budget: Budget[] = Object.values(bundle.budgets).map(value => ({
    area: value.area_id,
    low: value.cost_usd.low,
    high: value.cost_usd.high,
    unit: 'USD',
    assumptions: [...Object.entries(value.assumptions).map(([key, val]) => `${key}: ${String(val)}`), ...value.limits],
  }))

  return {
    meta: {
      run_id: bundle.generated_at ? `agents-${bundle.generated_at}` : 'unavailable',
      generated_at: bundle.generated_at,
      region: 'South Lebanon',
      change_delay_hours: 72,
      officer: 'Authenticated responder',
      availability: bundle.unavailable,
    },
    imagery: {
      with_token: 'Cesium ion imagery; capture date varies by tile, not the incident date',
      without_token: 'Esri World Imagery; capture date varies by tile, not the incident date',
    },
    passes: timeline,
    incidents,
    damage_cells: damageCells,
    change_cells: [],
    fires,
    nightlights,
    population,
    facilities: [],
    shelters: [],
    routes: [],
    budget,
    radar_layers: bundle.layers.items.flatMap(layer => layer.tile_url ? [{ id: layer.layer_id, title: layer.title ?? layer.product, tile_url: layer.tile_url, date: layer.date ?? layer.available_acquisitions.at(-1)?.slice(0, 10) ?? '', product: layer.product, attribution: layer.attribution ?? layer.product }] : []),
  }
}
