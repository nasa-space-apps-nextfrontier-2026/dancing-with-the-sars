import { useState } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { api, type Session } from '../services/api'
import { fixtures } from '../types/contracts'
import { EvidenceLabel, DataAge, SystemState } from '../components/Evidence'
import { MapPanel } from '../components/MapPanel'
import { AreaExplorer } from '../features/area/AreaExplorer'
import { useAuth } from './useAuth'

const pages = [
  ['/', 'Main map'], ['/alerts', 'Alert detail'], ['/areas', 'Area summary'], ['/brief', 'Area brief'],
  ['/routes', 'Routes'], ['/shelters', 'Shelters'], ['/inspector', 'Inspector'], ['/sources', 'Sources']
] as const

function PublicPreview() { return <section><h2>Public-safe preview</h2><p>Sign in for authorized area analysis. No routes, shelters, dispatch locations or sensitive facilities appear here.</p><MapPanel/><SystemState kind="unavailable" message="No approved public layers are loaded in this scaffold."/></section> }
function MainMap() { return <section><h2>NISAR change workspace</h2><p>January → June candidate comparison requires verified radar products. Source-reported gap: 20 January–17 June 2026; no passes are interpolated.</p><div className="map-grid"><aside><h3>Agent results</h3><SystemState kind="unavailable" message="No verified analysis yet."/><h3>Data layers</h3><p>NISAR CORE · HH / HV / HH−HV · no real raster loaded</p></aside><AreaExplorer/><aside><h3>Alert feed</h3><p>Synthetic example only</p><EvidenceLabel label={fixtures.alert.label}/><Link to="/alerts">Inspect example alert</Link></aside></div></section> }
function AlertDetail() { const a=fixtures.alert; return <section><h2>Alert detail</h2><p>{a.title}</p><EvidenceLabel label={a.label}/><DataAge freshness={a.freshness} cached={a.cached}/><p>{a.warning}</p><p>1 km and 3 km rings are reserved for authorized real data; this fixture has no coordinates.</p></section> }
function AreaSummary() { const a=fixtures.area; return <section><h2>Area summary</h2><p>People first: synthetic baseline {a.people.residents.low}–{a.people.residents.high} {a.people.residents.unit}.</p><EvidenceLabel label={a.people.residents.label}/><p>{a.warning}</p><h3>What to bring</h3><p>Verify reported services before supply planning. No quantities are inferred.</p></section> }
function AreaBrief() { return <section className="brief"><h2>Area brief · synthetic</h2><p>Printable A4 placeholder. Actual reports require server authorization and source footnotes.</p><button onClick={() => window.print()}>Print illustrative brief</button></section> }
function RouteScreen() { return <section><h2>Routes</h2><p>Local routing is not enabled. No origin, destination or live navigation is collected.</p><SystemState kind="unavailable" message="Route computation requires a private graph, current closures and authorization."/><p>{fixtures.route.warning}</p></section> }
function Shelters() { return <section><h2>Shelter candidates</h2><p>Restricted coordinator workflow. No real locations or capacity assessment are loaded.</p><SystemState kind="unavailable" message="Protection and explosive-ordnance field checks required before any use."/></section> }
function Inspector() { return <section><h2>Inspector</h2><nav aria-label="Inspector tabs">All agents · Time series · Validation</nav><SystemState kind="empty" message="No validated area result is available."/></section> }
function Sources() { return <section><h2>Sources and model checks</h2><p>NASA NISAR is the challenge core. Dataset dates and IDs in the planning catalogue are a 13 November 2026 source snapshot.</p><p>No granule or scientific model was tested by this scaffold.</p><Link to="/inspector">Trace a value placeholder</Link></section> }

function SignIn({onSignIn}:{onSignIn:(x:Session)=>void}) {
  const navigate = useNavigate()
  const [name,setName]=useState(''); const [password,setPassword]=useState(''); const [message,setMessage]=useState('')
  return <section><h2>Sign in</h2><p>Authorized demo roles are configured locally by the server. No default account is shipped.</p><form onSubmit={async e=>{e.preventDefault();setMessage('');try{onSignIn(await api.signIn(name,password));navigate('/')}catch{setMessage('Sign-in failed. Check local demo account setup.')}}}><label>Username<input value={name} onChange={e=>setName(e.target.value)} autoComplete="username"/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label><button>Sign in</button></form>{message && <SystemState kind="error" message={message}/>}</section>
}
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
  return <BrowserRouter><div className={`app ${theme}`}>
    <header><div><strong>CIVISAR</strong><span> NASA Space Apps ? Dancing with the SARs</span></div><div>
      <span className="demo-mark">Illustrative demo data</span>
      <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label="Toggle theme">{theme === 'light' ? 'Dark' : 'Light'} theme</button>
      {session ? <button onClick={() => { void signOut() }}>Sign out</button> : state.kind === 'checking' ? null : <Link to="/signin">Sign in</Link>}
    </div></header>
    <nav className="primary-nav" aria-label="Main navigation">{pages.map(([path, label]) => <Link key={path} to={path}>{label}</Link>)}</nav>
    <main>{state.kind === 'checking' ? <SystemState kind="loading" message="Checking session?" /> : <>
      {state.kind === 'expired' && <SystemState kind="error" message="Session expired. Sign in again." />}
      {state.kind === 'unavailable' && <div><SystemState kind="unavailable" message="Session status is unavailable. Protected content is hidden."/><button onClick={retry}>Retry session check</button></div>}
      <Routes>
        <Route path="/signin" element={session ? <Navigate to="/" replace /> : <SignIn onSignIn={signIn} />} />
        <Route path="/" element={session ? <MainMap /> : <PublicPreview />} />
        <Route path="/alerts" element={<Protected session={session} level={1}><AlertDetail /></Protected>} />
        <Route path="/areas" element={<Protected session={session} level={1}><AreaSummary /></Protected>} />
        <Route path="/brief" element={<Protected session={session} level={1}><AreaBrief /></Protected>} />
        <Route path="/routes" element={<Protected session={session} level={2}><RouteScreen /></Protected>} />
        <Route path="/shelters" element={<Protected session={session} level={3}><Shelters /></Protected>} />
        <Route path="/inspector" element={<Protected session={session} level={1}><Inspector /></Protected>} />
        <Route path="/sources" element={<Sources />} />
      </Routes>
    </>}</main>
    <footer>Development scaffold ? No operational guidance ? Field verification required</footer>
  </div></BrowserRouter>
}
