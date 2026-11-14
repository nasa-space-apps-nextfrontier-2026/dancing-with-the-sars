import { useEffect, useRef, useState } from 'react'
import { Map as LibreMap, type StyleSpecification } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

export type RadarMode = 'before' | 'after' | 'change' | 'swipe'
export type Polarization = 'HH' | 'HV' | 'HH-HV'
export type RadarView = { mode: RadarMode; polarization: Polarization; opacity: number; split: number }

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
        center: radar ? [0, 0] : [35.5, 33.3], zoom: radar ? 5 : 8,
        attributionControl: false,
      })
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
  </div>
}
