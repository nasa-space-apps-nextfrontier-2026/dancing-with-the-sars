// Pure rules for the "Change over time" panel (doc 34). No Cesium, no React: unit-tested.
// Drivers are always a hypothesis with alternatives; the wording never claims a result is settled or an area is without risk.
import type { ChangePoint, Range } from '../../types/map'

export type Polarization = 'HH' | 'HV' | 'HH-HV'
export type OkPoint = ChangePoint & { status: 'ok'; index: number }
export type Driver = { title: string; why: string; alternatives: string[]; confirm: string[]; warRelated: boolean }

export const POL_LABEL: Record<Polarization, string> = { HH: 'HH', HV: 'HV', 'HH-HV': 'HH−HV' }
export const POL_EXPLAIN: Record<Polarization, string> = {
  HH: 'Horizontal send, horizontal receive. Strongest from walls and ground forming corners (double bounce). Building collapse removes those corners, so HH drops.',
  HV: 'Cross-polarized. Comes from rough, messy surfaces and vegetation (volume scattering). Rubble can make HV rise; burnt orchards and fields make HV drop.',
  'HH-HV': 'The ratio. Separates structure lost (HH down more than HV) from vegetation lost (HV down more than HH).',
}

/** Thresholds from doc 34 §5. */
export const COLLAPSE_HH_DB = -2
export const RUBBLE_HV_DB = 0.5
export const HH_DROP_DB = -0.5
export const HV_DROP_DB = -0.3
export const RAIN_UP_DB = 0.8

/** Acquired passes, keeping their index in the full 32-date series. Missed passes are dropped, never filled. */
export function okPoints(series: ChangePoint[]): OkPoint[] {
  return series.flatMap((p, index) => (p.status === 'ok' ? [{ ...p, status: 'ok' as const, index }] : []))
}
export const missedCount = (series: ChangePoint[]) => series.filter(p => p.status === 'missed').length

/** Backscatter change vs the pre-war baseline for one polarization, or null when the pass has no value. */
export function polValue(p: ChangePoint, pol: Polarization): number | null {
  if (p.status !== 'ok') return null
  const v = pol === 'HH' ? p.hh_change_db : pol === 'HV' ? p.hv_change_db : p.ratio_change_db ?? (p.hh_change_db != null && p.hv_change_db != null ? p.hh_change_db - p.hv_change_db : undefined)
  return v == null || Number.isNaN(v) ? null : v
}

/** Runs of consecutive acquired passes: a line is drawn per run and never joined across a missed pass. */
export function segments(series: ChangePoint[], pol: Polarization): { index: number; value: number }[][] {
  const out: { index: number; value: number }[][] = []
  let run: { index: number; value: number }[] = []
  series.forEach((p, index) => {
    const value = polValue(p, pol)
    if (value == null) { if (run.length) out.push(run); run = []; return }
    run.push({ index, value })
  })
  if (run.length) out.push(run)
  return out
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
/** "2026-08-11" -> "11 Aug"; withYear -> "11 Aug 2026". */
export function shortDate(date: string, withYear = false) {
  const [y, m, d] = date.split('-').map(Number)
  return `${d} ${MONTHS[m - 1] ?? '?'}${withYear ? ` ${y}` : ''}`
}
export const fmtDb = (v: number | null | undefined) => (v == null ? 'Unknown' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)} dB`)

/** "$1.7–4 M (planning indication only)". */
export function budgetText(b: Range | undefined): string {
  if (!b) return 'Unknown (planning indication only)'
  const f = (n: number) => String(Math.round(n * 10) / 10)
  return `$${b.low === b.high ? f(b.low) : `${f(b.low)}–${f(b.high)}`} M (planning indication only)`
}

function dbPhrase(label: string, prev: number | null, cur: number | null) {
  if (prev == null || cur == null) return `${label} change is unknown on one of the passes`
  const d = cur - prev, a = Math.abs(d).toFixed(1)
  if (Math.abs(d) < 0.1) return `${label} stayed about the same`
  if (d < 0) return `${label} fell ${prev < 0 ? 'a further ' : ''}${a} dB`
  return `${label} rose ${prev > 0 ? 'a further ' : ''}${a} dB`
}

/** "Between 18 Jul and 11 Aug, candidate cells rose from 6 to 11; HH fell a further 0.9 dB." */
export function whatChanged(series: ChangePoint[], index: number, pol: Polarization = 'HH'): string {
  const cur = series[index]
  if (!cur || cur.status !== 'ok') return 'Missed pass: no new radar data from this date. Missing data is not evidence of no change.'
  const ok = okPoints(series), at = ok.findIndex(p => p.index === index), prev = at > 0 ? ok[at - 1] : null
  if (!prev) return `${shortDate(cur.date, true)} is the first pass in the series: the start of the pre-war baseline.`
  const a = prev.candidate_cells ?? 0, b = cur.candidate_cells ?? 0
  const cells = a === b ? `candidate cells stayed at ${b}` : `candidate cells ${b > a ? 'rose' : 'fell'} from ${a} to ${b}`
  const gap = index - prev.index - 1
  const missed = gap > 0 ? ` (${gap} missed pass${gap > 1 ? 'es' : ''} in between)` : ''
  return `Between ${shortDate(prev.date)} and ${shortDate(cur.date)}${missed}, ${cells}; ${dbPhrase(POL_LABEL[pol], polValue(prev, pol), polValue(cur, pol))}.`
}

/** Likely driver of the change at the current pass (doc 34 §5). Always "likely", with look-alikes and what would confirm it. */
export function driver(series: ChangePoint[], index: number, opts: { fireNearby?: boolean } = {}): Driver {
  const cur = series[index]
  if (!cur || cur.status !== 'ok') return {
    title: 'No data on this pass', why: 'NISAR did not acquire this date over the area. Nothing is filled in.',
    alternatives: [], confirm: ['The next acquired pass'], warRelated: false,
  }
  if (cur.tier === 'before') return {
    title: 'Pre-war baseline: seasonal change or noise', warRelated: false,
    why: 'Before the war the radar moves by a few tenths of a dB from pass to pass. This is the reference the later passes are compared with.',
    alternatives: ['Soil moisture after rain', 'Vegetation season'], confirm: ['The same small swings on the other pre-war passes'],
  }
  const ok = okPoints(series), at = ok.findIndex(p => p.index === index)
  const hh = cur.hh_change_db ?? 0, hv = cur.hv_change_db ?? 0
  const prev = at > 0 ? ok[at - 1] : null, next = at >= 0 && at < ok.length - 1 ? ok[at + 1] : null

  // Rain or soil moisture: both channels jump up for one pass, then come back.
  if (prev && next && (cur.hh_change_db ?? 0) - (prev.hh_change_db ?? 0) >= RAIN_UP_DB && (cur.hv_change_db ?? 0) - (prev.hv_change_db ?? 0) >= RAIN_UP_DB
    && Math.abs((next.hh_change_db ?? 0) - (prev.hh_change_db ?? 0)) < RAIN_UP_DB / 2) return {
    title: 'Likely not war-related: rain or soil moisture', warRelated: false,
    why: 'Both HH and HV rose for this one pass and were back on the next pass.',
    alternatives: ['Calibration error on this pass'], confirm: ['Rainfall recorded on that date'],
  }

  const base = baseDriver(ok.slice(0, at + 1), hh, hv, !!opts.fireNearby)
  if (!cur.quality) return base
  return {
    title: 'Suspect pass: read HH only', warRelated: base.warRelated,
    why: `This pass is marked ${cur.quality}. HV and HH−HV on this pass are not compared.`,
    alternatives: [base.title, ...base.alternatives], confirm: ['The next pass, processed normally', ...base.confirm],
  }
}

function baseDriver(upToNow: OkPoint[], hh: number, hv: number, fireNearby: boolean): Driver {
  const postWar = upToNow.filter(p => p.tier !== 'before')
  const lowPasses = postWar.filter(p => (p.hh_change_db ?? 0) <= COLLAPSE_HH_DB).length
  if (hh <= COLLAPSE_HH_DB && lowPasses >= 2) return {
    title: 'Likely building collapse (loss of double bounce)', warRelated: true,
    why: `HH is ${fmtDb(hh)} vs the pre-war baseline and has stayed at or below ${fmtDb(COLLAPSE_HH_DB)} on ${lowPasses} passes since the war began.`,
    alternatives: ['Demolition for construction', 'Wet season'], confirm: ['Optical image', 'Field report', 'Still low on the next pass'],
  }
  if (hh <= COLLAPSE_HH_DB) return {
    title: 'Possible building collapse, seen on one pass so far', warRelated: true,
    why: `HH is ${fmtDb(hh)} vs the pre-war baseline. It has not yet stayed low on a second pass.`,
    alternatives: ['Demolition for construction', 'Wet season', 'Noise on a single pass'], confirm: ['Still low on the next pass', 'Optical image'],
  }
  if (hv >= RUBBLE_HV_DB && hh <= HH_DROP_DB) return {
    title: 'Likely rubble and debris (rougher surface)', warRelated: true,
    why: `HV rose ${fmtDb(hv)} while HH fell ${fmtDb(hh)}: a rougher surface with fewer intact corners.`,
    alternatives: ['Construction sites', 'Crops growing'], confirm: ['Optical image of debris', 'Sentinel-1 agreement'],
  }
  if (hv <= HV_DROP_DB && fireNearby) return {
    title: 'Likely fire scar (burnt orchards, scrub)', warRelated: true,
    why: `HV fell ${fmtDb(hv)} near a fire detection: less vegetation to scatter the signal.`,
    alternatives: ['Harvest', 'Seasonal leaf loss'], confirm: ['FIRMS detection near the date', 'Optical burn scar'],
  }
  if (hv <= HV_DROP_DB) return {
    title: 'Vegetation loss or season (driver unclear)', warRelated: false,
    why: `HV fell ${fmtDb(hv)} with no fire detection nearby.`,
    alternatives: ['Harvest', 'Seasonal leaf loss', 'Fire not detected by satellite'], confirm: ['Same pattern in the pre-war passes', 'Optical image'],
  }
  return {
    title: 'Small change: driver unclear', warRelated: false,
    why: `HH ${fmtDb(hh)} and HV ${fmtDb(hv)} vs the baseline are close to the pre-war spread.`,
    alternatives: ['Noise', 'Soil moisture', 'Minor damage below what the radar resolves'], confirm: ['The next passes', 'Field report'],
  }
}
