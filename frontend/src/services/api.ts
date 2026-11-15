import type { MapData } from '../types/map'

export type ApiError = { error: { code: string; message: string; request_id: string; details: unknown[] }; synthetic: boolean }
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { credentials: 'include', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw data as ApiError
  return data as T
}

export type Role = 'analyst' | 'officer' | 'coordinator' | 'admin'
export type Session = { user_id: string; role: Role | string; area_scopes: string[]; csrf_token: string; synthetic: boolean; demo?: boolean }

/** A local demo session, used only when no backend is running. Always labelled as demo in the UI. */
export const demoSession = (): Session => ({ user_id: 'demo-officer', role: 'officer', area_scopes: ['south-lebanon'], csrf_token: '', synthetic: true, demo: true })

export const api = {
  health: () => request<{ status: string; synthetic: boolean }>('/health'),
  session: () => request<Session>('/session'),
  signIn: (username: string, password: string) =>
    request<Session>('/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }),
  signOut: (csrf: string) => request<unknown>('/session', { method: 'DELETE', headers: { 'X-CSRF-Token': csrf } }),
  /** Map data. Until the incident endpoints exist, this loads the sample file shaped like the API. */
  mapData: async (): Promise<{ data: MapData; sample: boolean }> => {
    const res = await fetch('/sample/civisar-3d-sample.json', { cache: 'no-store' })
    if (!res.ok) throw new Error('Sample map data not found')
    return { data: (await res.json()) as MapData, sample: true }
  },
}
