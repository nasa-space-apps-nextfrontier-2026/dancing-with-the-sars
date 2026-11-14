export function EvidenceLabel({label}:{label:string}) {
  return <span className="evidence" aria-label={`Evidence: ${label}`}>{label === 'Unknown' ? '◇' : label === 'Reported' ? '▢' : label === 'Corroborated' ? '◎' : '◉'} {label}</span>
}
export function DataAge({freshness,cached}:{freshness:string;cached:boolean}) {
  return <span className="age">{cached ? '◌ Cached' : freshness === 'Fresh' ? '● Fresh' : freshness === 'Aging' ? '○ Aging' : '◇ Stale'}</span>
}
export function SystemState({kind,message}:{kind:'loading'|'error'|'empty'|'stale'|'unavailable';message:string}) {
  return <p className={`system-state ${kind}`} role="status">{message}</p>
}
