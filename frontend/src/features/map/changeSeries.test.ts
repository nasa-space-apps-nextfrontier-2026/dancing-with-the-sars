import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { ChangePoint, MapData } from '../../types/map'
import { budgetText, driver, missedCount, okPoints, polValue, segments, whatChanged } from './changeSeries'

const sample = JSON.parse(readFileSync('public/sample/civisar-3d-sample.json', 'utf-8')) as MapData
const BANNED = /confirmed|safe/i

describe('sample series', () => {
  const series = sample.change_series!
  it('has 32 dates per incident: 17 acquired, 15 missed', () => {
    for (const s of Object.values(series.by_incident)) {
      expect(s).toHaveLength(32)
      expect(okPoints(s)).toHaveLength(17)
      expect(missedCount(s)).toBe(15)
    }
  })
  it('never joins the line across a missed pass', () => {
    const s = series.by_incident['inc-khiam']
    for (const seg of segments(s, 'HH')) {
      for (let k = 1; k < seg.length; k++) expect(seg[k].index).toBe(seg[k - 1].index + 1)
      for (const p of seg) expect(s[p.index].status).toBe('ok')
    }
    expect(segments(s, 'HH').length).toBeGreaterThan(1)
  })
  it('no driver text, for any pass or incident, says confirmed or safe', () => {
    for (const s of Object.values(series.by_incident)) {
      s.forEach((_, i) => {
        for (const fireNearby of [true, false]) {
          const d = driver(s, i, { fireNearby })
          expect([d.title, d.why, ...d.alternatives, ...d.confirm].join(' ')).not.toMatch(BANNED)
        }
        expect(whatChanged(s, i)).not.toMatch(BANNED)
      })
    }
  })
})

const pt = (date: string, tier: ChangePoint['tier'], cells: number, hh: number, hv: number, extra: Partial<ChangePoint> = {}): ChangePoint =>
  ({ date, status: 'ok', tier, candidate_cells: cells, hh_change_db: hh, hv_change_db: hv, ratio_change_db: hh - hv, ...extra })
const miss = (date: string): ChangePoint => ({ date, status: 'missed' })

it('polarization values and missed passes', () => {
  const p = pt('2026-01-01', 'after', 1, -2, 0.5)
  expect(polValue(p, 'HH')).toBe(-2)
  expect(polValue(p, 'HV')).toBe(0.5)
  expect(polValue(p, 'HH-HV')).toBe(-2.5)
  expect(polValue(miss('2026-01-13'), 'HH')).toBeNull()
})

it('writes the "what changed" sentence', () => {
  const s = [pt('2026-07-18', 'after', 6, -1.3, 0.2), pt('2026-08-11', 'later', 11, -2.2, 0.3)]
  expect(whatChanged(s, 1)).toBe('Between 18 Jul and 11 Aug, candidate cells rose from 6 to 11; HH fell a further 0.9 dB.')
  const gap = [s[0], miss('2026-07-30'), s[1]]
  expect(whatChanged(gap, 2)).toContain('(1 missed pass in between)')
  expect(whatChanged(gap, 1)).toMatch(/^Missed pass/)
  expect(whatChanged(s, 0)).toMatch(/first pass/)
})

it('drivers follow the doc 34 rules', () => {
  const before = pt('2025-11-08', 'before', 0, -0.2, 0.1)
  expect(driver([before], 0).title).toBe('Pre-war baseline: seasonal change or noise')
  const collapse = [before, pt('2026-06-24', 'after', 9, -2.1, 0.2), pt('2026-07-06', 'after', 9, -2.3, 0.3)]
  expect(driver(collapse, 1).title).toMatch(/^Possible building collapse/)
  expect(driver(collapse, 2).title).toMatch(/^Likely building collapse/)
  expect(driver([before, pt('2026-06-24', 'after', 4, -1.2, 0.8)], 1).title).toMatch(/rubble/)
  const fire = [before, pt('2026-06-24', 'after', 2, -0.4, -0.7)]
  expect(driver(fire, 1, { fireNearby: true }).title).toMatch(/fire scar/)
  expect(driver(fire, 1, { fireNearby: false }).title).not.toMatch(/fire scar/)
  const rain = [pt('2026-07-06', 'after', 2, -0.5, 0), pt('2026-07-18', 'after', 2, 0.6, 1), pt('2026-08-11', 'later', 2, -0.5, 0)]
  expect(driver(rain, 1).title).toMatch(/rain/)
  const suspect = [...collapse, pt('2026-08-23', 'later', 9, -2.2, 2.5, { quality: 'suspect: HV about 2 dB too bright on this pass' })]
  expect(driver(suspect, 3).title).toMatch(/^Suspect pass/)
  for (const d of [driver(collapse, 2), driver(rain, 1), driver(suspect, 3)]) {
    expect(d.alternatives.length + d.confirm.length).toBeGreaterThan(0)
  }
})

it('budget text', () => {
  expect(budgetText({ low: 1.7, high: 4 })).toBe('$1.7–4 M (planning indication only)')
  expect(budgetText({ low: 0, high: 0 })).toBe('$0 M (planning indication only)')
  expect(budgetText(undefined)).toMatch(/Unknown/)
})
