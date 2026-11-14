// Pure helpers: distances, ranges and the per-incident impact analysis. No Cesium here, so it is unit-testable.
import type { DamageCell, Evidence, Facility, Fire, Incident, LonLat, MapData, NightCell, Path, Range, Shelter } from '../../types/map'

export const NEAR_M = 300
export const AREA_M = 1500

export const dist = (a: LonLat, b: LonLat) =>
  Math.hypot((a.lon - b.lon) * 111320 * Math.cos((a.lat * Math.PI) / 180), (a.lat - b.lat) * 111320)
export const fmt = (n: number) => n.toLocaleString('en-US')
export const rng = (r: Range) => (r.low === r.high ? fmt(r.low) : `${fmt(r.low)}–${fmt(r.high)}`)
export const fmtM = (m: number) => (m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`)
export const addHours = (d: string, h: number) => new Date(Date.parse(d + 'T00:00:00Z') + h * 3600e3).toISOString().slice(0, 10)

export const passIndex = (d: MapData, id: string) => d.passes.findIndex(p => p.id === id)
export const visibleAt = (d: MapData, passIdx: number) => (x: { pass_id?: string }) => !x.pass_id || passIndex(d, x.pass_id) <= passIdx

export type Hazard = { kind: 'damage' | 'fire' | 'power'; inside: boolean; m: number; ev: Evidence }

export type Analysis = {
  cells: DamageCell[]; fires: Fire[]; dark: NightCell[]
  facilities: { f: Facility; hz: Hazard[] }[]
  roads: MapData['routes']
  shelters: { s: Shelter; m: number; hz: Hazard[] }[]
  darkPeople: Range
  fireNear: { f: Fire; fac: Facility[]; cells: DamageCell[] }[]
  budget?: MapData['budget'][number]
  hazardsAt: (pt: LonLat) => Hazard[]
}

export function analyse(d: MapData, inc: Incident, passIdx: number): Analysis {
  const vis = visibleAt(d, passIdx)
  const here = (x: LonLat) => dist(x, inc) <= AREA_M
  const cells = d.damage_cells.filter(c => c.incident_id === inc.id && vis(c))
  const fires = d.fires.filter(f => here(f) && vis(f))
  const dark = d.nightlights.filter(n => n.state === 'dark' && here(n) && vis(n))
  const hazardsAt = (pt: LonLat): Hazard[] => {
    const out: Hazard[] = []
    const dm = cells.map(c => ({ c, m: dist(c, pt) - c.size_m / 2 })).sort((a, b) => a.m - b.m)[0]
    if (dm && dm.m <= NEAR_M) out.push({ kind: 'damage', inside: dm.m <= 0, m: Math.max(0, Math.round(dm.m)), ev: dm.c.evidence })
    const fr = fires.map(f => ({ f, m: dist(f, pt) })).sort((a, b) => a.m - b.m)[0]
    if (fr && fr.m <= fr.f.uncertainty_m) out.push({ kind: 'fire', inside: true, m: Math.round(fr.m), ev: fr.f.evidence })
    const dk = dark.map(n => ({ n, m: dist(n, pt) - n.size_m / 2 })).sort((a, b) => a.m - b.m)[0]
    if (dk && dk.m <= NEAR_M) out.push({ kind: 'power', inside: dk.m <= 0, m: Math.max(0, Math.round(dk.m)), ev: dk.n.sensors_agree ? 'Corroborated' : 'Observed' })
    return out
  }
  return {
    cells, fires, dark, hazardsAt,
    facilities: d.facilities.filter(here).map(f => ({ f, hz: hazardsAt(f) })).filter(x => x.hz.length > 0),
    roads: d.routes.filter(r => r.incident_id === inc.id && r.status === 'possibly_blocked_candidate'),
    shelters: d.shelters.filter(s => s.incident_id === inc.id).map(s => ({ s, m: Math.round(dist(s, inc)), hz: hazardsAt(s) })).sort((a, b) => a.m - b.m),
    darkPeople: dark.reduce((a, n) => ({ low: a.low + n.people.low, high: a.high + n.people.high }), { low: 0, high: 0 }),
    fireNear: fires.map(f => ({ f, fac: d.facilities.filter(x => dist(x, f) <= f.uncertainty_m), cells: cells.filter(c => dist(c, f) <= f.uncertainty_m) })),
    budget: d.budget.find(b => b.area === inc.name),
  }
}

export type PathStats = { pts: LonLat[]; near: boolean[]; len: number; blocked: boolean; touches: boolean }
/** Marks the parts of a road route that pass close to a visible damage candidate. */
export function pathStats(d: MapData, p: Path, passIdx: number): PathStats {
  const vis = visibleAt(d, passIdx)
  const cells = d.damage_cells.filter(vis)
  const pts = p.coords.map(([lon, lat]) => ({ lon, lat }))
  const near = pts.map(q => cells.some(c => dist(c, q) <= c.size_m / 2 + 35))
  const len = pts.slice(1).reduce((a, q, i) => a + dist(pts[i], q), 0)
  const blocked = p.status === 'possibly_blocked_candidate'
  return { pts, near, len, blocked, touches: blocked || near.some(Boolean) }
}
/** Splits a path into runs of "clear" and "near damage" segments. */
export function runs(pts: LonLat[], near: boolean[]) {
  const out: { f: boolean; pts: LonLat[] }[] = []
  let cur: { f: boolean; pts: LonLat[] } | null = null
  for (let i = 0; i < pts.length - 1; i++) {
    const f = near[i] || near[i + 1]
    if (!cur || cur.f !== f) { cur = { f, pts: [pts[i]] }; out.push(cur) }
    cur.pts.push(pts[i + 1])
  }
  return out
}

export function rawPaths(d: MapData): Path[] {
  return [
    ...d.routes.map(r => ({ id: r.id, kind: 'route' as const, incident_id: r.incident_id, label: r.label, status: r.status, coords: r.coords, source: 'sample' as const })),
    ...d.shelters.map(s => {
      const inc = d.incidents.find(i => i.id === s.incident_id)!
      return { id: 'to-' + s.id, kind: 'shelter' as const, shelter_id: s.id, incident_id: s.incident_id, label: 'To ' + s.name.replace(/ \(OSM\)$/, ''),
        status: 'available_not_verified' as const, coords: [[inc.lon, inc.lat], [s.lon, s.lat]] as [number, number][], source: 'direct' as const }
    }),
  ]
}

/** Decimal degrees to D°MM′SS.S″ */
export function dms(v: number, pos: string, neg: string) {
  const a = Math.abs(v), d = Math.floor(a), m = Math.floor((a - d) * 60), s = ((a - d) * 60 - m) * 60
  return `${d}°${String(m).padStart(2, '0')}′${s.toFixed(1).padStart(4, '0')}″${v >= 0 ? pos : neg}`
}
