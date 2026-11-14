export type ApiError = { error: { code: string; message: string; request_id: string; details: unknown[] }; synthetic: boolean }
const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { credentials: 'include', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw data as ApiError
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
}
