import { useEffect, useState } from 'react'
import { api, type Session } from '../services/api'
import { SignIn } from '../features/signin/SignIn'
import { MapScreen } from '../features/map/MapScreen'

/** Login is required: the map only renders for a signed-in session. */
export function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let live = true
    api.session().then(s => { if (live) setSession(s) }).catch(() => {}).finally(() => { if (live) setChecking(false) })
    return () => { live = false }
  }, [])

  async function signOut() {
    if (session && !session.demo) await api.signOut(session.csrf_token).catch(() => {})
    setSession(null)
  }

  if (checking) return <main className="signin"><span className="muted small">Checking session…</span></main>
  if (!session) return <SignIn onSignIn={setSession} />
  return <MapScreen session={session} onSignOut={signOut} />
}
