import { useEffect, useRef, useState } from 'react'
<<<<<<< ours
import { Map as LibreMap, NavigationControl, ScaleControl, setWorkerUrl } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import type { Layer, RadarObservation } from '../types/contracts'
=======
import { Map as LibreMap, setWorkerUrl, type StyleSpecification } from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
>>>>>>> theirs
import 'maplibre-gl/dist/maplibre-gl.css'

setWorkerUrl(mapWorkerUrl)

export type RadarMode = 'before' | 'after' | 'change' | 'swipe'
export type Polarization = 'HH' | 'HV' | 'HH-HV'
export type RadarView = { mode: RadarMode; polarization: Polarization; opacity: number; split: number }

<<<<<<< ours
export const BASEMAP_STYLE_URL = import.meta.env.VITE_BASEMAP_STYLE_URL
  || 'https://tiles.openfreemap.org/styles/liberty'

export function canRenderAnalyticalRaster(layer?: Layer, observation?: RadarObservation) {
  return Boolean(layer?.extent && layer?.tile_url && observation?.raster_available
    && observation.valid_pixel_count > 0)
}

export function MapPanel({ onSelectDemoArea, radar, layer, observation }: {
  onSelectDemoArea?: () => void
  radar?: RadarView
  layer?: Layer
  observation?: RadarObservation
}) {
  const node = useRef<HTMLDivElement>(null)
  const [failure, setFailure] = useState(false)
  const rasterReady = canRenderAnalyticalRaster(layer, observation)

  useEffect(() => {
    if (!node.current) return
    setFailure(false)
    try {
      const map = new LibreMap({
        container: node.current,
        style: BASEMAP_STYLE_URL,
        center: [35.48, 33.25],
        zoom: node.current.clientWidth < 600 ? 7.4 : 8.35,
        minZoom: 5,
        maxZoom: 16,
        attributionControl: true,
      })
      map.addControl(new NavigationControl({ showCompass: true, visualizePitch: true }), 'top-right')
      map.addControl(new ScaleControl({ unit: 'metric', maxWidth: 120 }), 'bottom-left')
      map.on?.('error', event => {
        console.error('MapLibre render failed', event.error)
        setFailure(true)
      })
      map.on?.('load', () => {
        if (!rasterReady || !layer || !observation) return
        map.addSource('civisar-analysis', {
          type: 'raster', tiles: [layer.tile_url], tileSize: 256, attribution: layer.attribution,
        })
        map.addLayer({
          id: 'civisar-analysis', type: 'raster', source: 'civisar-analysis',
          paint: { 'raster-opacity': (radar?.opacity ?? 75) / 100 },
        })
      })
      return () => map.remove()
    } catch (error) {
      console.error('MapLibre initialization failed', error)
      setFailure(true)
    }
  }, [layer, observation, radar?.opacity, rasterReady])

  const date = observation ? new Date(observation.acquired_at).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC',
  }) : null
  return <div className="map-wrap">
    <div ref={node} className="map" role="img" aria-label={
      `Geographic map of south Lebanon${date ? `; selected catalogue acquisition ${date}` : ''}; `
      + (rasterReady ? 'analytical raster displayed' : 'analytical raster unavailable')
    } />
    <div className="map-badge">{rasterReady
      ? `${radar?.polarization ?? 'HH'} analytical raster · ${date}`
      : 'Geographic context · Analytical raster unavailable'}</div>
    {onSelectDemoArea && <button className="map-select" onClick={onSelectDemoArea}>Select demo analysis area</button>}
    {failure && <p className="map-fallback">Basemap could not be loaded. Observation metadata remains accessible.</p>}
=======
function syntheticGrid() {
  const features = Array.from({ length: 48 }, (_, index) => {
    const column = index % 8
    const row = Math.floor(index / 8)
    const left = -1.2 + column * .3
    const bottom = -.9 + row * .3
    const wave = ((column * 7 + row * 11) % 17) / 20
    const beforeHH = .2 + wave
    const beforeHV = .1 + wave * .7
    const afterHH = Math.min(1, beforeHH + ((column + row) % 5 - 2) * .09)
    const afterHV = Math.min(1, beforeHV + ((column * 2 + row) % 5 - 2) * .07)
    return {
      type: 'Feature' as const,
      properties: {
        column, beforeHH, beforeHV, afterHH, afterHV,
        'beforeHH-HV': beforeHH - beforeHV,
        'afterHH-HV': afterHH - afterHV,
        changeHH: .5 + (afterHH - beforeHH),
        changeHV: .5 + (afterHV - beforeHV),
        'changeHH-HV': .5 + (afterHH - afterHV) - (beforeHH - beforeHV),
      },
      geometry: { type: 'Polygon' as const, coordinates: [[
        [left, bottom], [left + .29, bottom], [left + .29, bottom + .29],
        [left, bottom + .29], [left, bottom],
      ]] },
    }
  })
  return { type: 'FeatureCollection' as const, features }
}

function fill(field: string) {
  return ['interpolate', ['linear'], ['get', field], 0, '#244d66', .5, '#90bdc7', 1, '#f7d881']
}

export function syntheticRadarStyle(view: RadarView): StyleSpecification {
  const splitColumn = Math.round(view.split / 100 * 8) - 1
  const layer = (id: string, field: string, filter?: unknown) => ({
    id, type: 'fill', source: 'synthetic-radar',
    ...(filter ? { filter } : {}),
    paint: { 'fill-color': fill(field), 'fill-opacity': view.opacity / 100,
      'fill-outline-color': '#234457' },
  })
  return {
    version: 8,
    sources: { 'synthetic-radar': { type: 'geojson', data: syntheticGrid() } },
    layers: [
      { id: 'background', type: 'background', paint: { 'background-color': '#d8e4eb' } },
      ...(view.mode === 'swipe'
        ? [layer('synthetic-before', `before${view.polarization}`,
          ['<=', ['get', 'column'], splitColumn]),
          layer('synthetic-after', `after${view.polarization}`,
            ['>', ['get', 'column'], splitColumn])]
        : [layer('synthetic-' + view.mode, `${view.mode}${view.polarization}`)]),
    ],
  } as StyleSpecification
}

export function MapPanel({ onSelectDemoArea, radar }: {
  onSelectDemoArea?: () => void; radar?: RadarView
}) {
  const node = useRef<HTMLDivElement>(null)
  const [failure, setFailure] = useState(false)
  useEffect(() => {
    if (!node.current) return
    try {
      const map = new LibreMap({
        container: node.current,
        style: radar ? syntheticRadarStyle(radar) : {
          version: 8, sources: {}, layers: [{ id: 'background', type: 'background',
            paint: { 'background-color': '#d8e4eb' } }],
        },
        center: radar ? [0, 0] : [35.5, 33.3], zoom: radar ? (node.current.clientWidth < 600 ? 6 : 7.5) : 8,
        attributionControl: false,
      })
      map.on?.('error', event => { console.error('MapLibre render failed', event.error); setFailure(true) })
      return () => map.remove()
    } catch { setFailure(true) }
  }, [radar])
  return <div className="map-wrap">
    <div ref={node} className="map" role="img" aria-label={radar
      ? `Non-georeferenced synthetic radar grid: ${radar.mode}, ${radar.polarization}`
      : 'Synthetic blank map canvas; no satellite imagery or operational locations loaded'} />
    <div className="map-badge">{radar
      ? 'Synthetic grid · Not NISAR imagery · No geographic position'
      : 'Illustrative demo data · No imagery loaded'}</div>
    {onSelectDemoArea && <button className="map-select" onClick={onSelectDemoArea}>Select synthetic demo area</button>}
    {failure && <p className="map-fallback">Map renderer unavailable. Area list remains accessible.</p>}
>>>>>>> theirs
  </div>
}
