import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

vi.mock('maplibre-gl', () => ({ Map: class { remove() {} } }))

import { App } from './App'
afterEach(cleanup)
describe('public-safe shell',()=>{
  it('labels synthetic content and never shows a shelter coordinate',()=>{
    render(<App/>)
    expect(screen.getAllByText(/Illustrative demo data/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/No approved public layers/)).toBeTruthy()
    expect(screen.queryByText(/Synthetic candidate A/)).toBeNull()
  })
})
