import type { SourceRecord } from '../../services/api'
import { Icon } from '../../components/Icons'

export type SourceCatalogueState =
  | { status: 'loading'; items: SourceRecord[]; error: '' }
  | { status: 'ready'; items: SourceRecord[]; error: '' }
  | { status: 'error'; items: SourceRecord[]; error: string }

function acquisition(record: SourceRecord): string {
  if (!record.acquisition_start && !record.acquisition_end) return 'Acquisition date unavailable'
  if (record.acquisition_start === record.acquisition_end) return record.acquisition_start
  return `${record.acquisition_start || 'Unknown'} – ${record.acquisition_end || 'Unknown'}`
}

function publicUrl(value: string): string | null {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : null
  } catch {
    return null
  }
}

export function SourcesPanel({ catalogue, onClose }: { catalogue: SourceCatalogueState; onClose: () => void }) {
  return <>
    <div className="dh"><div style={{ flex: 1, minWidth: 0 }}><span className="kicker">Evidence provenance</span><h2>Sources</h2></div>
      <button className="x" aria-label="Close panel" onClick={onClose}><Icon name="close" size={20} /></button></div>
    <div className="db">
      {catalogue.status === 'loading' && <p className="empty" role="status">Loading source catalogue…</p>}
      {catalogue.status === 'error' && <div className="note" role="alert"><Icon name="info" size={16} /><span>{catalogue.error}</span></div>}
      {catalogue.status === 'ready' && catalogue.items.length === 0 && <p className="empty">No approved source records are available.</p>}
      {catalogue.items.length > 0 && <ul className="list">{catalogue.items.map(source => {
        const sourceUrl = publicUrl(source.source_url)
        return <li key={source.source_id} className="card">
        <div className="row" style={{ alignItems: 'flex-start' }}><h3 style={{ flex: 1 }}>{source.name}</h3>
          {source.synthetic && <span className="tag">Synthetic</span>}
          <span className="tag">{source.live_tested ? 'Live-tested' : 'Not live-tested'}</span></div>
        <p className="small muted">{source.provider} · {source.dataset_id} · {source.product_level}</p>
        <dl className="kv">
          <dt>Acquisition</dt><dd>{acquisition(source)}</dd>
          <dt>Maturity</dt><dd>{source.product_level || 'Unknown'} · {source.live_tested ? 'Live-tested' : 'Not live-tested'}</dd>
          <dt>Processing</dt><dd>{source.processing_version || 'Unknown'}</dd>
          <dt>Provenance</dt><dd>{source.challenge_provenance || source.independence_family || 'Unknown'}</dd>
          <dt>Coverage</dt><dd>{source.spatial_coverage.area_id || 'Unknown'} · track {source.spatial_coverage.track} · frame {source.spatial_coverage.frame}</dd>
          <dt>Resolution</dt><dd>{source.resolution_m == null ? 'Unknown' : `${source.resolution_m} m`}</dd>
          <dt>Licence</dt><dd>{source.licence}</dd>
          <dt>Access</dt><dd>{source.api || 'Unknown'}{source.accessed_at ? ` · ${source.accessed_at}` : ''}</dd>
        </dl>
        {source.limits.length > 0 && <><div className="sect" style={{ margin: '10px 0 4px' }}>Limitations</div>
          <ul className="small" style={{ margin: 0, paddingLeft: 18 }}>{source.limits.map(limit => <li key={limit}>{limit}</li>)}</ul></>}
        {sourceUrl && <p style={{ marginBottom: 0 }}><a className="linkbtn" href={sourceUrl} target="_blank" rel="noreferrer">Open provider record</a></p>}
      </li>})}</ul>}
    </div>
  </>
}
