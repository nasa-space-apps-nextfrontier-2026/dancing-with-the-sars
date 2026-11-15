import type { MapData } from '../types/map'
import { toMapData, type FrontendMapBundle } from './mapData'

export type ApiError = { error: { code: string; message: string; request_id: string; details: unknown[] }; synthetic: boolean }
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export function apiErrorMessage(value: unknown, fallback = 'The requested data is unavailable.'): string {
  const typed = value as Partial<ApiError> | null
  if (typed?.error?.message) return typed.error.message
  if (value instanceof Error && value.message) return value.message
  return fallback
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { credentials: 'include', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw data as ApiError
  return data as T
}

export type Role = 'analyst' | 'officer' | 'coordinator' | 'admin'
export type Session = { user_id: string; role: Role | string; area_scopes: string[]; csrf_token: string; synthetic: boolean; demo?: boolean }
export type SourceRecord = {
  synthetic: boolean
  source_id: string
  dataset_id: string
  name: string
  provider: string
  product_level: string
  cmr_concept_id: string
  challenge_provenance: string
  source_url: string
  acquisition_start: string
  acquisition_end: string
  processing_version: string
  spatial_coverage: { area_id: string; geometry: unknown; track: number; frame: number }
  resolution_m: number | null
  licence: string
  accessed_at: string | null
  api: string
  checksum: string | null
  independence_family: string
  live_tested: boolean
  limits: string[]
}
export type SourceList = { synthetic: boolean; items: SourceRecord[]; next_cursor: string | null }

/** A local demo session, used only when no backend is running. Always labelled as demo in the UI. */
export const demoSession = (): Session => ({ user_id: 'demo-officer', role: 'officer', area_scopes: ['south-lebanon'], csrf_token: '', synthetic: true, demo: true })

export const api = {
  health: () => request<{ status: string; synthetic: boolean }>('/health'),
  sources: (cursor?: string) => request<SourceList>(`/sources${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`),
  sourceCatalogue: async (): Promise<SourceRecord[]> => {
    const items: SourceRecord[] = []
    let cursor: string | undefined
    for (let pageNumber = 0; pageNumber < 100; pageNumber += 1) {
      const page = await api.sources(cursor)
      items.push(...page.items)
      if (!page.next_cursor) return items
      cursor = page.next_cursor
    }
    throw new Error('Source catalogue pagination did not terminate.')
  },
  session: () => request<Session>('/session'),
  signIn: (username: string, password: string) =>
    request<Session>('/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }),
  signOut: (csrf: string) => request<unknown>('/session', { method: 'DELETE', headers: { 'X-CSRF-Token': csrf } }),
  /** Demo sessions use the labelled fixture; real sessions use only released, scoped API data. */
  mapData: async (session: Session): Promise<{ data: MapData; sample: boolean }> => {
    if (!session.synthetic) {
      const bundle = await request<FrontendMapBundle>('/map/context?limit=100')
      return { data: toMapData(bundle), sample: false }
    }
    const response = await fetch('/sample/civisar-3d-sample.json', { cache: 'no-store' })
    if (!response.ok) throw new Error('Sample map data not found')
    return { data: (await response.json()) as MapData, sample: true }
  },
}
