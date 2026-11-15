import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import css from './landing.css?inline'
import { LANDING_MARKUP } from './markup'
import { initLanding } from './landingScene'
import { usePageStyle } from '../../app/usePageStyle'

/** Public landing page: 3D Earth story, sections and links into the dashboard (/map). No sign-in. */
export function Landing() {
  usePageStyle(css, 'landing')
  const root = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    document.title = 'RescueForce'
    if (!root.current) return
    let stop: (() => void) | undefined
    try { stop = initLanding(root.current, path => navigate(path)) }
    catch (err) { console.warn('Landing scene could not start', err) }   // page text and links still work without WebGL
    return () => stop?.()
  }, [navigate])

  return <div ref={root} className="rf-landing" dangerouslySetInnerHTML={{ __html: LANDING_MARKUP }} />
}
