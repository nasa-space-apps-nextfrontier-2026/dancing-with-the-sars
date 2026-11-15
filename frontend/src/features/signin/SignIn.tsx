import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, type ApiError } from '../../services/api'
import { Logo } from '../../components/Icons'
import css from '../../styles.css?inline'
import { usePageStyle } from '../../app/usePageStyle'

/** Sign-in for real data (doc 07: login required). The public dashboard shows labelled sample data only. */
export function SignIn() {
  usePageStyle(css, 'signin')
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(''); setBusy(true)
    try {
      await api.signIn(username.trim(), password)
      navigate('/map')
    } catch (err) {
      const code = (err as ApiError)?.error?.code
      setError(code ? 'Sign-in failed. Check your username and password.' : 'The RescueForce server is not reachable.')
    } finally { setBusy(false) }
  }

  return (
    <main className="signin">
      <form className="signin-card glass" onSubmit={submit} aria-labelledby="signin-title">
        <div className="brandrow"><span className="logo"><Logo /></span><b>RescueForce</b><span className="muted small">South Lebanon</span></div>
        <span className="kicker">Restricted · responders only</span>
        <h1 id="signin-title">Sign in</h1>
        <p className="muted small">Real damage, alerts, facilities and people ranges are shown to signed-in responders only, within their own area.</p>
        <label className="field"><span>Username</span>
          <input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required autoFocus /></label>
        <label className="field"><span>Password</span>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        {error && <div className="err" role="alert">{error}</div>}
        <button className="btn primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <Link className="btn ghost" to="/map">Continue with sample data</Link>
        <div className="signin-foot">
          <span>Accounts are set up by your coordinator. No default account is shipped.</span>
          <span>No live vehicle or phone tracking. Everything on the map is a candidate until checked on the ground.</span>
        </div>
      </form>
    </main>
  )
}
