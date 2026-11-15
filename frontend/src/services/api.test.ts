import { afterEach, expect, it, vi } from 'vitest'
import { request } from './api'
afterEach(()=>vi.unstubAllGlobals())

it.each([
  [401, 'UNAUTHORIZED'],
  [403, 'FORBIDDEN'],
  [422, 'VALIDATION_ERROR'],
  [503, 'SERVICE_UNAVAILABLE'],
])('preserves the typed API error for HTTP %i', async (status, code) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({ error: { code, message: 'Unavailable', request_id: 'demo', details: [] }, synthetic: false }),
  }))
  await expect(request('/map/context')).rejects.toMatchObject({ error: { code } })
})
