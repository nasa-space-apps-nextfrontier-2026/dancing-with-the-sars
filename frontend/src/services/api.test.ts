import { afterEach, expect, it, vi } from 'vitest'
import { api, apiErrorMessage, request } from './api'
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

it('renders a useful message for typed API and network failures', () => {
  expect(apiErrorMessage({ error: { message: 'Released map data is unavailable.' } })).toBe('Released map data is unavailable.')
  expect(apiErrorMessage(new Error('Network request failed'))).toBe('Network request failed')
  expect(apiErrorMessage({})).toBe('The requested data is unavailable.')
})

it('loads the public source catalogue through the typed client', async () => {
  const first = { synthetic: false, items: [{ source_id: 'one' }], next_cursor: '1' }
  const second = { synthetic: false, items: [{ source_id: 'two' }], next_cursor: null }
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => first })
    .mockResolvedValueOnce({ ok: true, json: async () => second })
  vi.stubGlobal('fetch', fetchMock)
  await expect(api.sourceCatalogue()).resolves.toEqual([...first.items, ...second.items])
  expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/v1/sources', expect.objectContaining({ credentials: 'include' }))
  expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/v1/sources?cursor=1', expect.objectContaining({ credentials: 'include' }))
})
