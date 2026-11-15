import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'

vi.mock('cesium', () => ({}))
vi.mock('../features/map/MapScreen', () => ({ MapScreen: () => <main><h1>RescueForce dashboard</h1></main> }))

import { App } from './App'

afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.history.pushState({}, '', '/') })

it('opens the public dashboard at /map without a sign-in wall', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  window.history.pushState({}, '', '/map')
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'RescueForce dashboard' })).toBeTruthy()
  expect(screen.queryByRole('heading', { name: 'Sign in' })).toBeNull()
})
