// Shapes of the map data. They mirror docs/design/civisar-3d-sample.json, which is shaped like the future API.
export type Evidence = 'Observed' | 'Reported' | 'Corroborated' | 'Unknown'
export type DamageClass = 'destroyed' | 'severe' | 'moderate' | 'possible'
export type Range = { low: number; high: number }
export type LonLat = { lon: number; lat: number; h?: number }

export type Pass = { id: string; date: string; sensor: string; status: 'ok' | 'missed' }
export type AssistantOption = { title: string; trade_off: string; why: string[]; needs: string[]; risks: string[] }
/** The decision assistant's own output (agent U-05): options, not orders. */
export type Assistant = { situation: string; options: AssistantOption[]; unknowns: string[]; next_review: [string, string][]; note: string }
export type Suggestion = { id: string; kind: 'check' | 'route'; text: string; reason: string }
export type Incident = LonLat & {
  id: string; name: string; area: string; rank: number; score: Range; damage_class: DamageClass; evidence: Evidence
  second_sensor_agrees: boolean; first_pass: string; buildings_candidate: Range; people_nearby: Range
  buildings_available?: boolean; people_available?: boolean
  /** Facility counts by type in the area (real data only, when the API sends them). */
  facility_counts?: Record<string, number>
  why: { factor: string; value: string; weight: number }[]
  insights: { text: string; evidence: Evidence; source: string; source_date: string }[]
  suggestions: Suggestion[]
  assistant?: Assistant
  /** When the satellite saw it (radar pass or alert detection), not when it was processed. */
  acquired_at?: string
}
export type DamageCell = LonLat & { id: string; incident_id: string; size_m: number; damage_class: DamageClass; evidence: Evidence; second_sensor: boolean; pass_id: string }
export type ChangeCell = LonLat & { id: string; size_m: number; pass_id: string }
export type Fire = LonLat & { id: string; detected_at: string; source: string; evidence: Evidence; uncertainty_m: number; pass_id: string }
export type NightCell = LonLat & { id: string; size_m: number; state: 'dark' | 'lit'; pass_id: string; last_lit: string | null; sensors_agree: boolean; people: Range; people_available?: boolean }
export type PopCell = LonLat & { id: string; size_m: number; people: Range }
export type Facility = LonLat & { id: string; kind: string; name: string }
export type Shelter = LonLat & { id: string; incident_id: string; kind: string; name: string; capacity: Range }
export type Route = { id: string; incident_id: string; label: string; status: 'available_not_verified' | 'possibly_blocked_candidate'; coords: [number, number][] }
export type Budget = { area: string; low: number; high: number; unit: string; assumptions: string[]; label?: string; duration_months?: Range }
export type RadarLayer = { id: string; title: string; tile_url: string; date: string; product: string; attribution: string }

export type MapData = {
  meta: { run_id: string; generated_at: string; region: string; change_delay_hours: number; officer: string; availability?: Record<string, string> }
  imagery: { with_token: string; without_token: string }
  passes: Pass[]; incidents: Incident[]; damage_cells: DamageCell[]; change_cells: ChangeCell[]; fires: Fire[]
  nightlights: NightCell[]; population: PopCell[]; facilities: Facility[]; shelters: Shelter[]; routes: Route[]; budget: Budget[]
  radar_layers?: RadarLayer[]
}

export type LayerKey = 'damage' | 'second' | 'change' | 'fires' | 'night' | 'pop' | 'facilities' | 'shelters' | 'routes' | 'streets' | 'buildings'
export type Layers = Record<LayerKey, boolean>
export type ViewMode = '2d' | '3d' | 'split'
export type BaseMap = 'sat' | 'streets'

/** A road route: from the data ("route") or incident -> candidate shelter ("shelter"). */
export type Path = {
  id: string; kind: 'route' | 'shelter'; incident_id: string; shelter_id?: string; label: string
  status: Route['status']; coords: [number, number][]; source: 'sample' | 'direct' | 'osm'
}
