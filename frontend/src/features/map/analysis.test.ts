import { describe, expect, it } from 'vitest'
import sample from '../../../public/sample/civisar-3d-sample.json'
import type { MapData } from '../../types/map'
import { analyse, dms, pathStats, rawPaths, rng } from './analysis'

const D = sample as unknown as MapData
const khiam = D.incidents.find(i => i.id === 'inc-khiam')!

describe('analysis', () => {
  it('shows ranges, not single numbers', () => {
    expect(rng({ low: 1800, high: 2900 })).toBe('1,800–2,900')
  })
  it('finds shelters and facilities near hazards for an incident', () => {
    const a = analyse(D, khiam, 4)
    expect(a.shelters.length).toBe(3)
    expect(a.facilities.length).toBeGreaterThan(0)
    expect(a.roads.every(r => r.status === 'possibly_blocked_candidate')).toBe(true)
  })
  it('hides damage that appears after the selected pass', () => {
    expect(analyse(D, khiam, 0).cells.length).toBe(0)
  })
  it('marks a candidate-blocked road as blocked', () => {
    const ridge = rawPaths(D).find(p => p.id === 'rK')!
    expect(pathStats(D, ridge, 4).touches).toBe(true)
  })
  it('formats coordinates as DMS', () => {
    expect(dms(33.3372, 'N', 'S')).toBe('33°20′13.9″N')
  })
})
