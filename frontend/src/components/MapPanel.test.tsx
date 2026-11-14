import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

vi.mock('maplibre-gl', () => ({ Map: class { remove() {} }, setWorkerUrl: vi.fn() }))

import { AreaExplorer } from '../features/area/AreaExplorer'
import { syntheticRadarStyle } from './MapPanel'

afterEach(cleanup)

describe('synthetic radar comparison', () => {
  it('changes MapLibre source paint and swipe filters with controls', () => {
    const base = {mode:'before' as const,polarization:'HH' as const,opacity:75,split:50}
    const before = syntheticRadarStyle(base)
    expect(Object.keys(before.sources)).toEqual(['synthetic-radar'])
    expect(before.layers[1].id).toBe('synthetic-before')
    const hv = syntheticRadarStyle({...base,mode:'after',polarization:'HV',opacity:40})
    expect(hv.layers[1].id).toBe('synthetic-after')
    expect(JSON.stringify(hv.layers[1])).toContain('afterHV')
    expect(JSON.stringify(hv.layers[1])).toContain('0.4')
    const swipe = syntheticRadarStyle({...base,mode:'swipe',split:25})
    expect(swipe.layers.map(layer => layer.id)).toContain('synthetic-after')
    expect(JSON.stringify(swipe.layers)).toContain('column')
  })

  it('shows gap and changes visible mode and polarization', () => {
    render(<AreaExplorer />)
    expect(screen.getByText(/20 Jan–17 Jun 2026/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:'After'}))
    expect(screen.getByText(/After window: 24 Jun/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:'HV'}))
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('after, HV')
    fireEvent.click(screen.getByRole('button',{name:'Swipe'}))
    expect(screen.getByLabelText(/Swipe split/)).toBeTruthy()
  })
})
