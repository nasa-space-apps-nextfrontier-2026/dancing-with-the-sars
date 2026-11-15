import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('cesium', () => ({}))
vi.mock('../features/landing/landingScene', () => ({ initLanding: () => () => {} }))   // no WebGL in jsdom
import { App } from './App'

afterEach(() => { cleanup(); window.history.pushState({}, '', '/') })
describe('public routes', () => {
  it('opens on the landing page with links into the map and no sign-in', async () => {
    render(<App />)
    expect((await screen.findByRole('heading', { level: 1 })).textContent).toMatch(/War damages more/)
    const links = Array.from(document.querySelectorAll('a[data-link]')).map(a => a.getAttribute('href'))
    expect(links.length).toBeGreaterThan(0)
    expect(links.every(h => h === '/map')).toBe(true)
    expect(document.body.textContent).not.toMatch(/sign in|password/i)
  })
  it('sends unknown paths back to the landing page', async () => {
    window.history.pushState({}, '', '/signin')
    render(<App />)
    await screen.findByRole('heading', { level: 1 })
    expect(window.location.pathname).toBe('/')
  })
})
