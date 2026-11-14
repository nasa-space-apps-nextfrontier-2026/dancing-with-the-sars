import { useState } from 'react'
import { api, demoSession, type ApiError, type Session } from '../../services/api'
import { Logo } from '../../components/Icons'

/** Sign-in is required. Uses the backend cookie session; a labelled demo session is offered when no backend runs. */
export function SignIn({ onSignIn }: { onSignIn: (s: Session) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [offline, setOffline] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(''); setBusy(true)
    try { onSignIn(await api.signIn(username.trim(), password)) }
    catch (err) {
      const code = (err as ApiError)?.error?.code
      if (code) setError('Sign-in failed. Check your username and password.')
      else { setOffline(true); setError('The CIVISAR server is not reachable.') }
    } finally { setBusy(false) }
  }

  return (
    <main className="signin">
      <form className="signin-card glass" onSubmit={submit} aria-labelledby="signin-title">
        <div className="brandrow"><span className="logo"><Logo /></span><b>CIVISAR</b><span className="muted small">South Lebanon</span></div>
        <span className="kicker">Restricted · responders only</span>
        <h1 id="signin-title">Sign in</h1>
        <p className="muted small">Damage, routes and shelter candidates are shown to signed-in responders only.</p>
        <label className="field"><span>Username</span>
          <input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required autoFocus /></label>
        <label className="field"><span>Password</span>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        {error && <div className="err" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        {offline && <button type="button" className="btn ghost" onClick={() => onSignIn(demoSession())}>Continue with demo session (sample data)</button>}
        <div className="signin-foot">
          <span>Accounts are set up by your coordinator. No default account is shipped.</span>
          <span>No live vehicle or phone tracking. Everything on the map is a candidate until checked on the ground.</span>
        </div>
      </form>
    </main>
  )
}
