import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('cesium', () => ({}))
import { App } from './App'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })
describe('sign-in gate', () => {
  it('shows the sign-in screen, not the map, when there is no session', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'No session', request_id: 't', details: [] }, synthetic: true }) }))
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeTruthy()
    expect(screen.queryByText(/Fly to top incident/)).toBeNull()
    expect(document.body.textContent).not.toMatch(/\bsafe\b/i)
  })
})
