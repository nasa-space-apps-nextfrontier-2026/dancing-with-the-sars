import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

// Each page loads its own code: the landing page never downloads Cesium, the dashboard never downloads three.js.
const Landing = lazy(() => import('../features/landing/Landing').then(m => ({ default: m.Landing })))
const MapScreen = lazy(() => import('../features/map/MapScreen').then(m => ({ default: m.MapScreen })))

/** Two public routes, no sign-in: the landing page and the dashboard (labelled sample data). */
export function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div style={{ position: 'fixed', inset: 0, background: '#05070a' }} />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/map" element={<MapScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
