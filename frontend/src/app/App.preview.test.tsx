import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'

vi.mock('cesium', () => ({}))
vi.mock('../config/runtime', () => ({ localPreview: true }))
vi.mock('../features/map/MapScreen', () => ({
  MapScreen: ({ session }: { session: { synthetic: boolean; demo?: boolean } }) => (
    <main><h1>CIVISAR dashboard</h1><span>{session.synthetic && session.demo ? 'Sample data' : 'Unexpected session'}</span></main>
  ),
}))

import { App } from './App'

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

it('opens the dashboard without requesting a session in local preview', () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  expect(screen.getByRole('heading', { name: 'CIVISAR dashboard' })).toBeTruthy()
  expect(screen.getByText('Sample data')).toBeTruthy()
  expect(screen.queryByRole('heading', { name: 'Sign in' })).toBeNull()
  expect(fetchMock).not.toHaveBeenCalled()
})
