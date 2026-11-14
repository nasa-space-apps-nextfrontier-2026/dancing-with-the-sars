import { useEffect, useRef, useState } from 'react'
import { Map as LibreMap } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

export function MapPanel() {
  const node = useRef<HTMLDivElement>(null)
  const [failure,setFailure] = useState(false)
  useEffect(() => {
    if (!node.current) return
    try {
      const map = new LibreMap({ container: node.current,
        style: { version: 8, sources: {}, layers: [{id:'background',type:'background',paint:{'background-color':'#d8e4eb'}}] },
        center: [35.5,33.3], zoom: 8, attributionControl: false })
      return () => map.remove()
    } catch { setFailure(true) }
  }, [])
  return <div className="map-wrap"><div ref={node} className="map" role="img" aria-label="Synthetic blank map canvas; no satellite imagery or operational locations loaded"/><div className="map-badge">Illustrative demo data · No imagery loaded</div>{failure && <p className="map-fallback">Map renderer unavailable. Area list remains accessible.</p>}</div>
}
