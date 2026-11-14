import type { AreaSummary, SourceRecord } from '../types/contracts'

export type ApiError = { error: { code: string; message: string; request_id: string; details: unknown[] }; synthetic: boolean }
export const UNAUTHENTICATED_EVENT = 'civisar:unauthenticated'
export function apiErrorCode(value: unknown): string | undefined {
  if (typeof value !== 'object' || value === null || !('error' in value)) return undefined
  const detail = value.error
  return typeof detail === 'object' && detail !== null && 'code' in detail && typeof detail.code === 'string'
    ? detail.code : undefined
}
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { credentials: 'include', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401 && !(path === '/session' && options.method === 'POST')) {
      window.dispatchEvent(new Event(UNAUTHENTICATED_EVENT))
    }
    throw data as ApiError
  }
  return data as T
}
export type Session = { user_id: string; role: string; area_scopes: string[]; csrf_token: string; synthetic: boolean }
export const api = {
  health: () => request<{status:string;synthetic:boolean}>('/health'),
  status: () => request<{synthetic:boolean;sources:unknown[];message:string}>('/status'),
  publicMap: () => request<{synthetic:boolean;layers:unknown[];suppressed:boolean}>('/public/map'),
  signIn: (username:string,password:string) => request<Session>('/session',{
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}),
  signOut: (csrf:string) => request<unknown>('/session',{method:'DELETE',headers:{'X-CSRF-Token':csrf}}),
  session: () => request<Session>('/session'),
  areaSummary: (areaId:string) => request<AreaSummary>(`/areas/${encodeURIComponent(areaId)}/summary`),
  sourceRecord: (sourceId:string) => request<SourceRecord>(`/sources/${encodeURIComponent(sourceId)}`),
}
