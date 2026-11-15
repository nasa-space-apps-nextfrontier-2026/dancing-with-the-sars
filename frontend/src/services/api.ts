import type { MapData } from '../types/map'

export type ApiError = { error: { code: string; message: string; request_id: string; details: unknown[] }; synthetic: boolean }
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { credentials: 'include', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw data as ApiError
  return data as T
}

export const api = {
  health: () => request<{ status: string; synthetic: boolean }>('/health'),
  /** Map data. Until the incident endpoints exist, this loads the sample file shaped like the API. */
  mapData: async (): Promise<{ data: MapData; sample: boolean }> => {
    const res = await fetch('/sample/civisar-3d-sample.json', { cache: 'no-store' })
    if (!res.ok) throw new Error('Sample map data not found')
    return { data: (await res.json()) as MapData, sample: true }
  },
}
