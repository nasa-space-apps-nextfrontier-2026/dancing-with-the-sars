import { useEffect, useState } from 'react'
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { type Session } from '../services/api'
import { SystemState } from '../components/Evidence'
import { MapPanel } from '../components/MapPanel'
import { PrototypeMain } from '../features/prototype/PrototypeMain'
import { useAuth } from './useAuth'
import { PrototypeIcon } from '../components/PrototypeIcon'
import { PrototypeSources } from '../features/prototype/PrototypeSources'
import { PrototypeAlert, PrototypeArea, PrototypeBrief, PrototypeRoutes, PrototypeShelters, PrototypeInspector, PrototypeSignIn, PrototypePhone } from '../features/prototype/PrototypeViews'

function PublicPreview() { return <section><h2>Public-safe preview</h2><p>Sign in for authorized area analysis. No routes, shelters, dispatch locations or sensitive facilities appear here.</p><MapPanel/><SystemState kind="unavailable" message="No approved public layers are loaded in this scaffold."/></section> }
function MainMap() { return <PrototypeMain /> }
function Protected({session,level,children}:{session:Session|null;level:number;children:React.ReactNode}) {
  const roleLevel:Record<string,number>={analyst:1,officer:2,coordinator:3,admin:4}
  if (!session) return <Navigate to="/signin" replace/>
  if ((roleLevel[session.role]||0)<level) return <SystemState kind="error" message="Your role cannot access this view."/>
  return <>{children}</>
}
export function App() {
  const { state, signIn, signOut, retry } = useAuth()
  const session = state.kind === 'signed_in' ? state.session : null
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  useEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  return <BrowserRouter><div className={`app prototype ${theme}`}>
    <header className="cv-top prototype-header">
      <Link to="/" className="cv-brand" aria-label="CIVISAR main map"><svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><rect width="26" height="26" rx="6" fill="var(--accent)"/><path d="M6 19a13 13 0 0 1 13-13M10 19a9 9 0 0 1 9-9M14 19a5 5 0 0 1 5-5" fill="none" stroke="var(--ink-inverse)" strokeWidth="2" strokeLinecap="round"/><circle cx="19" cy="19" r="2.2" fill="var(--ink-inverse)"/></svg><span>CIVISAR<small>powered by NASA NISAR</small></span></Link>
      <nav className="cv-tabs prototype-nav" aria-label="Main navigation"><NavLink to="/" end>Map</NavLink><NavLink to="/alerts">Alerts</NavLink><NavLink to="/areas">Areas</NavLink><NavLink to="/routes">Routes</NavLink><NavLink to="/shelters">Shelters</NavLink><NavLink to="/sources">Sources</NavLink><details><summary>More</summary><div><Link to="/brief">Area brief</Link><Link to="/inspector">Inspector</Link><Link to="/phone">Phone preview</Link></div></details></nav>
      <div className="cv-input prototype-search" aria-label="Search unavailable"><PrototypeIcon name="search"/>Search place or alert</div>
      <div className="prototype-header-spacer"/>
      <div className="cv-fresh" aria-label="Source freshness unavailable">{['NISAR','SENTINEL-1','NIGHT LIGHTS','FIRES','INTERNET'].map(name=><span key={name}>{name}<small>Unknown</small></span>)}</div>
      <button className="cv-btn cv-btn--ghost cv-btn--icon" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label="Toggle theme"><PrototypeIcon name={theme==='light'?'moon':'sun'}/></button>
      {session ? <div className="prototype-account"><span className="cv-avatar">{session.user_id.slice(0,2).toUpperCase()}</span><span className="cv-col"><b>{session.user_id}</b><small>{session.role}</small></span><button className="cv-btn cv-btn--sm" onClick={() => { void signOut() }}>Sign out</button></div> : state.kind === 'checking' ? null : <Link className="cv-btn cv-btn--primary" to="/signin"><PrototypeIcon name="lock"/>Sign in</Link>}
    </header>
    <main>{state.kind === 'checking' ? <SystemState kind="loading" message="Checking session…" /> : <>
      {state.kind === 'expired' && <SystemState kind="error" message="Session expired. Sign in again." />}
      {state.kind === 'unavailable' && <div><SystemState kind="unavailable" message="Session status is unavailable. Protected content is hidden."/><button onClick={retry}>Retry session check</button></div>}
      <Routes>
        <Route path="/signin" element={session ? <Navigate to="/" replace /> : <PrototypeSignIn onSignIn={signIn} />} />
        <Route path="/" element={session ? <MainMap /> : <PublicPreview />} />
        <Route path="/alerts" element={<Protected session={session} level={1}><PrototypeAlert /></Protected>} />
        <Route path="/areas" element={<Protected session={session} level={1}><PrototypeArea /></Protected>} />
        <Route path="/brief" element={<Protected session={session} level={1}><PrototypeBrief /></Protected>} />
        <Route path="/routes" element={<Protected session={session} level={2}><PrototypeRoutes /></Protected>} />
        <Route path="/shelters" element={<Protected session={session} level={3}><PrototypeShelters /></Protected>} />
        <Route path="/inspector" element={<Protected session={session} level={1}><PrototypeInspector /></Protected>} />
        <Route path="/sources" element={<PrototypeSources />} />
        <Route path="/phone" element={<PrototypePhone />} />
      </Routes>
    </>}</main>
    <footer>Development scaffold · No operational guidance · Field verification required</footer>
  </div></BrowserRouter>
}
