import { useEffect, useState } from 'react'
import { api, apiErrorCode, UNAUTHENTICATED_EVENT, type Session } from '../services/api'

type AuthState =
  | { kind: 'checking' | 'signed_out' | 'expired' | 'unavailable' }
  | { kind: 'signed_in'; session: Session }

const roles = new Set(['analyst', 'officer', 'coordinator', 'admin'])
function validSession(session: Session): boolean {
  return typeof session.user_id === 'string' && roles.has(session.role) &&
    typeof session.csrf_token === 'string' && Array.isArray(session.area_scopes) &&
    session.area_scopes.every(scope => typeof scope === 'string')
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({ kind: 'checking' })

  useEffect(() => {
    let active = true
    function onExpired() {
      setState(previous => previous.kind === 'signed_in' ? { kind: 'expired' } : previous)
    }
    window.addEventListener(UNAUTHENTICATED_EVENT, onExpired)
    api.session().then(session => {
      if (active) setState(validSession(session) ? { kind: 'signed_in', session } : { kind: 'unavailable' })
    }).catch(failure => {
      if (active) setState({ kind: apiErrorCode(failure) === 'UNAUTHENTICATED' ? 'signed_out' : 'unavailable' })
    })
    return () => { active = false; window.removeEventListener(UNAUTHENTICATED_EVENT, onExpired) }
  }, [])

  function signIn(session: Session) {
    setState(validSession(session) ? { kind: 'signed_in', session } : { kind: 'unavailable' })
  }

  async function signOut() {
    if (state.kind !== 'signed_in') return
    const csrf = state.session.csrf_token
    setState({ kind: 'signed_out' }) // Remove protected view before the request completes.
    try {
      await api.signOut(csrf)
    } catch {
      setState({ kind: 'unavailable' }) // Server revocation could not be confirmed.
    }
  }

  function retry() {
    setState({ kind: 'checking' })
    api.session().then(session => {
      setState(validSession(session) ? { kind: 'signed_in', session } : { kind: 'unavailable' })
    }).catch(failure => {
      setState({ kind: apiErrorCode(failure) === 'UNAUTHENTICATED' ? 'signed_out' : 'unavailable' })
    })
  }

  return { state, signIn, signOut, retry }
}
