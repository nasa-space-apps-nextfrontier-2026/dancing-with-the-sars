import { useEffect, useState } from 'react'
import { localPreview } from '../config/runtime'
import { api, demoSession, type Session } from '../services/api'
import { SignIn } from '../features/signin/SignIn'
import { MapScreen } from '../features/map/MapScreen'

/** Production uses the session gate; local preview uses a labelled synthetic session. */
export function App() {
  const [session, setSession] = useState<Session | null>(() => localPreview ? demoSession() : null)
  const [checking, setChecking] = useState(!localPreview)

  useEffect(() => {
    if (localPreview) return
    let live = true
    api.session().then(s => { if (live) setSession(s) }).catch(() => {}).finally(() => { if (live) setChecking(false) })
    return () => { live = false }
  }, [])

  async function signOut() {
    if (localPreview) {
      setSession(demoSession())
      return
    }
    if (session && !session.demo) await api.signOut(session.csrf_token).catch(() => {})
    setSession(null)
  }

  if (checking) return <main className="signin"><span className="muted small">Checking session…</span></main>
  if (!session) return <SignIn onSignIn={setSession} />
  return <MapScreen session={session} onSignOut={signOut} />
}
