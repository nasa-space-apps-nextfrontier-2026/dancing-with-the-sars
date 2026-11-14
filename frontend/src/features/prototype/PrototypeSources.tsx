import { useState } from 'react'
import { PrototypeIcon } from '../../components/PrototypeIcon'

const catalogue = [
  ['NISAR GCOV / GSLC','NASA–ISRO','Radar change candidates','NASA'],
  ['OPERA RTC-S1','NASA / ESA','Cross-check radar change','NASA'],
  ['FIRMS VIIRS','NASA','Fire alerts','NASA'],
  ['OpenStreetMap','OSM contributors','Roads, buildings, facilities','Other'],
  ['WorldPop','Univ. of Southampton','Population baseline','Other'],
  ['ACLED','ACLED','Conflict events and corroboration','Other'],
  ['IODA','Georgia Tech','Internet outages','Other'],
  ['IOM DTM · Meta movement','IOM · Meta Data for Good','Displacement and movement','Other'],
  ['Insecurity Insight','Insecurity Insight','Attacks on health, water, schools','Other'],
  ['UNOSAT · UNDP','UNITAR · UNDP','Analyst validation','Other'],
] as const

export function PrototypeSources() {
  const [filter,setFilter] = useState('All')
  const [query,setQuery] = useState('')
  const [selected,setSelected] = useState('NISAR GCOV / GSLC')
  const rows = catalogue.filter(row => (filter==='All'||row[3]===filter) && row.join(' ').toLowerCase().includes(query.toLowerCase()))
  return <section id="v-sources" className="prototype-screen" aria-label="Sources and citations">
    <div className="prototype-screen-wrap prototype-sources-grid"><div>
      <h1 className="cv-h1">Sources and citations</h1>
      <p className="cv-sm cv-muted">Every value must trace to a dataset, a date and an evidence label. NASA data is the base of CIVISAR.</p>
      <p className="cv-eyebrow">NASA DATA</p>
      <div className="prototype-source-tiles">{['NISAR · core','OPERA RTC-S1','Black Marble','FIRMS VIIRS','NASADEM','NASA GIBS'].map((name,index)=><article className={`tile ${index===0?'core':''}`} key={name}><b>{name}</b><span className="cv-xs">{index===0?'L-band SAR · NASA–ISRO':index===1?'Sentinel-1 radar change':index===2?'Night lights, NOAA-20/21':index===3?'Active fires':index===4?'Terrain for open land':'Base maps'}</span><span className="cv-data">Availability unverified</span></article>)}</div>
      <div className="prototype-source-tools"><span className="cv-eyebrow">ALL DATASETS</span><div className="cv-row">{['All','NASA','Other'].map(name=><button key={name} className={`cv-tag ${filter===name?'is-on':''}`} aria-pressed={filter===name} onClick={()=>setFilter(name)}>{name}</button>)}<label className="prototype-filter"><PrototypeIcon name="search"/><input aria-label="Filter datasets" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Filter"/></label></div></div>
      <table className="cv-table prototype-source-table"><thead><tr><th>DATASET</th><th>PROVIDER</th><th>USED FOR</th><th>NEWEST</th><th>LABEL</th></tr></thead><tbody>{rows.map(row=><tr key={row[0]} tabIndex={0} aria-selected={selected===row[0]} className={selected===row[0]?'is-sel':''} onClick={()=>setSelected(row[0])} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(row[0])}}}><td><b>{row[0]}</b></td><td>{row[1]}</td><td>{row[2]}</td><td>Unverified</td><td><span className="cv-ev cv-ev--unk">Unknown</span></td></tr>)}</tbody></table>
      <p className="cv-xs cv-muted">Catalogue names and intended uses follow the prototype. No live dataset or freshness claim is made.</p>
    </div><aside className="prototype-screen-aside">
      <div className="box"><span className="cv-eyebrow">TRACE A VALUE</span><h2 className="cv-h2">{selected}</h2><p className="cv-sm">No reviewed output or provenance chain is loaded for this catalogue entry.</p><span className="cv-ev cv-ev--unk">Unknown</span></div>
      <div className="box"><span className="cv-eyebrow">CITE</span><p className="cv-data">Source catalogue snapshot · 13 Nov 2026. Verify dataset IDs, processing versions and licensing before publication.</p></div>
      <div className="box"><span className="cv-eyebrow">EVIDENCE LABELS</span>{['Observed','Reported','Corroborated','Unknown'].map(name=><div className="cv-row prototype-evidence-row" key={name}><span className={`cv-ev cv-ev--${{Observed:'obs',Reported:'rep',Corroborated:'cor',Unknown:'unk'}[name as 'Observed'|'Reported'|'Corroborated'|'Unknown']}`}>{name}</span><span className="cv-xs">{name==='Unknown'?'No reviewed evidence loaded':'Requires a reviewed source'}</span></div>)}</div>
    </aside></div>
  </section>
}
