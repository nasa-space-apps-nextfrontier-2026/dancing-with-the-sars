// "Change over time" panel (doc 34): how one area changed after every NISAR pass. Pure SVG, no Cesium.
import { useEffect, useId, useMemo, useState, type ReactNode } from 'react'
import type { ChangePoint, ChangeSeries, Evidence, Incident, MapData } from '../../types/map'
import { Icon } from '../../components/Icons'
import { AREA_M, dist } from './analysis'
import {
  budgetText, driver, fmtDb, missedCount, okPoints, POL_EXPLAIN, POL_LABEL, polValue, segments, shortDate, whatChanged, type Polarization,
} from './changeSeries'

const POLS: Polarization[] = ['HH', 'HV', 'HH-HV']
const STEP_MS = 1200
const W = 340, PL = 30, PR = 26, CH = 150, BH = 64

type Props = { data: MapData; incident: Incident | null; sample: boolean; onPick: (id: string) => void; onClose: () => void }

export function ChangeOverTime({ data, incident, sample, onPick, onClose }: Props) {
  const cs = data.change_series
  const head = <div className="dh"><div style={{ flex: 1, minWidth: 0 }}><span className="kicker" title={sample ? data.change_series?._note : undefined}>Change over time{sample ? ' · Sample data' : ''}</span>
    <h2>{incident ? incident.name : 'Pick an area'}</h2></div>
    <button className="x" aria-label="Close panel" onClick={onClose}><Icon name="close" size={20} /></button></div>
  const series = incident ? cs?.by_incident[incident.id] : undefined

  if (!incident || !cs || !series?.length) return <>{head}<div className="db">
    {incident
      ? <p style={{ marginTop: 0 }}>No pass-by-pass series is available for this area. Missing data is not evidence of no change.</p>
      : <p style={{ marginTop: 0 }}>See how an area changed after every NISAR pass, which polarization shows it and the likely cause. Pick an area:</p>}
    <div className="cot-pick">
      {data.incidents.filter(i => i.id !== incident?.id).sort((a, b) => a.rank - b.rank).map(i =>
        <button key={i.id} className="btn sm" onClick={() => onPick(i.id)}>{i.name}{cs?.by_incident[i.id] ? '' : ' · no series'}</button>)}
    </div>
    <div style={{ marginTop: 10 }}><Note>Archive analysis, updated per satellite pass. Not live detection.</Note></div>
  </div></>

  const fireNearby = data.fires.some(f => dist(f, incident) <= AREA_M)
  return <>{head}<SeriesView key={incident.id} cs={cs} series={series} incident={incident} fireNearby={fireNearby} /></>
}

function Note({ children }: { children: ReactNode }) {
  return <div className="note"><Icon name="info" size={16} /><span>{children}</span></div>
}

function SeriesView({ cs, series, incident, fireNearby }: { cs: ChangeSeries; series: ChangePoint[]; incident: Incident; fireNearby: boolean }) {
  const ok = useMemo(() => okPoints(series), [series])
  const [okIdx, setOkIdx] = useState(Math.max(0, ok.length - 1))
  const [pol, setPol] = useState<Polarization>('HH')
  const [playing, setPlaying] = useState(false)
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '')

  useEffect(() => {
    if (!playing) return
    const t = setInterval(() => setOkIdx(i => {
      if (i >= ok.length - 1) { setPlaying(false); return i }
      return i + 1
    }), STEP_MS)
    return () => clearInterval(t)
  }, [playing, ok.length])

  if (!ok.length) return <div className="db"><Note>No acquired passes for this area. Missing data is not evidence of no change.</Note></div>
  const cur = ok[Math.min(okIdx, ok.length - 1)]
  const index = cur.index
  const toggle = () => {
    if (playing) { setPlaying(false); return }
    if (okIdx >= ok.length - 1) setOkIdx(0)
    setPlaying(true)
  }
  const pick = (i: number) => { const k = ok.findIndex(p => p.index === i); if (k >= 0) { setPlaying(false); setOkIdx(k) } }
  const evidence: Evidence = incident.second_sensor_agrees ? 'Corroborated' : 'Observed'
  const drv = driver(series, index, { fireNearby })
  const missed = missedCount(series)

  return <div className="db cot">
    <div className="row" style={{ marginBottom: 8 }}>
      <span className="tag cot-area" title={cs.baseline}>{cs.study_area}</span>
    </div>

    <div className="cot-seg" role="group" aria-label="Polarization">
      {POLS.map(p => <button key={p} aria-pressed={pol === p} onClick={() => setPol(p)} title={POL_EXPLAIN[p]}>{POL_LABEL[p]}</button>)}
    </div>

    <ChangeChart series={series} cs={cs} pol={pol} index={index} uid={uid} onPick={pick} />
    <div className="cot-legend small muted">
      <span><i className="sw bar" />Candidate cells</span><span><i className="sw line" />{POL_LABEL[pol]} vs baseline</span>
      <span><i className="sw miss" />Missed ({missed})</span><span><i className="sw sus" />Suspect</span>
    </div>

    <div className="sect">Rebuild budget over time</div>
    <BudgetChart series={series} index={index} onPick={pick} />
    <p className="small muted" style={{ margin: '2px 0 0' }}>Range in million USD, recalculated with the damage seen up to each pass. Planning indication only.</p>

    <div className="cot-play">
      <button className="btn sm" aria-pressed={playing} aria-label={playing ? 'Pause pass playback' : 'Play passes'} disabled={ok.length < 2} onClick={toggle}>{playing ? 'Pause' : 'Play'}</button>
      <input type="range" min={0} max={ok.length - 1} step={1} value={okIdx} aria-label="Satellite pass"
        aria-valuetext={`${shortDate(cur.date, true)}, pass ${okIdx + 1} of ${ok.length} acquired`}
        onChange={e => { setPlaying(false); setOkIdx(+e.target.value) }} />
      <span className="mono small">{okIdx + 1}/{ok.length}</span>
    </div>
    <p className="small muted" style={{ margin: '0 0 8px' }}>Play and the slider step through acquired passes only; missed passes are skipped, never filled in. Tap a column to jump to it.</p>

    <div className="kpis">
      <div className="kpi"><span className="k">Pass</span><b>{shortDate(cur.date, true)}</b><span className="s">{cur.tier === 'before' ? 'Before the war (baseline)' : cur.tier === 'after' ? 'After' : 'Later pass'}</span></div>
      <div className="kpi"><span className="k">Candidate cells</span><b>{cur.candidate_cells ?? 'Unknown'}</b><span className="s">Damage candidates, not facts</span></div>
      <div className="kpi"><span className="k">HH / HV</span><b>{fmtDb(polValue(cur, 'HH'))} / {fmtDb(polValue(cur, 'HV'))}</b><span className="s">Change vs pre-war baseline</span></div>
      <div className="kpi"><span className="k">Budget</span><b>{cur.budget_musd ? budgetText(cur.budget_musd).split(' (')[0] : 'Unknown'}</b><span className="s">Planning indication only</span></div>
    </div>
    {cur.quality && <div style={{ marginTop: 8 }}><Note><b style={{ color: 'var(--ink)' }}>Suspect pass.</b> {cur.quality}.</Note></div>}

    <div className="sect">What changed</div>
    <p className="cot-what" aria-live="polite">{whatChanged(series, index, pol)}</p>

    <div className="sect">Why the radar changed</div>
    <div className="cot-why">
      <div className="row" style={{ marginBottom: 6 }}><span className={`chip ev-${evidence}`}>{evidence}</span>
        <span className="tag">{drv.warRelated ? 'Hypothesis' : 'Likely not war-related'}</span></div>
      <b>{drv.title}</b>
      <p className="small">{drv.why}</p>
      {drv.alternatives.length > 0 && <p className="small"><span className="muted">Look-alikes to rule out: </span>{drv.alternatives.join(' · ')}</p>}
      <p className="small"><span className="muted">What would confirm it: </span>{drv.confirm.join(' · ')}</p>
    </div>

    <div className="sect">Polarizations</div>
    <div className="cot-explain">
      {POLS.map(p => <div key={p} className={pol === p ? 'on' : undefined}><span className="tag">{POL_LABEL[p]}</span><span className="small">{POL_EXPLAIN[p]}</span></div>)}
    </div>
    <div style={{ marginTop: 10 }}><Note>Archive analysis, updated per satellite pass (12-day repeat). Causes are likely, not settled: check before acting.</Note></div>
  </div>
}

const colX = (i: number, n: number) => PL + ((W - PL - PR) / n) * (i + 0.5)
const colW = (n: number) => (W - PL - PR) / n

function ChangeChart({ series, cs, pol, index, uid, onPick }: { series: ChangePoint[]; cs: ChangeSeries; pol: Polarization; index: number; uid: string; onPick: (i: number) => void }) {
  const n = series.length, cw = colW(n)
  const vals = series.map(p => polValue(p, pol)).filter((v): v is number => v != null)
  const lo = Math.floor(Math.min(-1, ...vals)), hi = Math.ceil(Math.max(1, ...vals))
  const top = 14, bottom = CH - 18
  const y = (v: number) => top + ((hi - v) / (hi - lo)) * (bottom - top)
  const maxCells = Math.max(1, ...series.map(p => p.candidate_cells ?? 0))
  const barH = (c: number) => (c / maxCells) * (bottom - top) * 0.55
  const gapA = series.findIndex(p => p.date >= cs.war_gap.from), gapB = series.reduce((last, p, i) => (p.date <= cs.war_gap.to ? i : last), -1)
  const ticks = Array.from({ length: hi - lo + 1 }, (_, k) => hi - k).filter(t => (hi - lo) <= 6 || t % 2 === 0)
  const cur = series[index]
  const label = `Chart of ${n} pass dates: candidate cells as bars and ${POL_LABEL[pol]} change vs baseline as a line. ${missedCount(series)} missed passes shown as gaps. Current pass ${cur ? shortDate(cur.date, true) : ''}.`
  const years = series.map((p, i) => ({ i, y: p.date.slice(0, 4) })).filter((p, k, a) => k === 0 || a[k - 1].y !== p.y)

  return <svg className="cot-chart" viewBox={`0 0 ${W} ${CH}`} role="img" aria-label={label}>
    <defs><pattern id={`h${uid}`} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="var(--ink-4)" strokeWidth="1.2" /></pattern></defs>
    {gapA >= 0 && gapB >= gapA && <g>
      <rect x={colX(gapA, n) - cw / 2} y={top} width={cw * (gapB - gapA + 1)} height={bottom - top} fill="rgba(255,255,255,.035)" />
      <text x={colX(gapA, n) - cw / 2 + (cw * (gapB - gapA + 1)) / 2} y={top + 10} className="cot-t" textAnchor="middle"><title>{cs.war_gap.note}</title>War period · no passes</text>
    </g>}
    {ticks.map(t => <g key={t}><line x1={PL} x2={W - PR} y1={y(t)} y2={y(t)} stroke={t === 0 ? 'var(--stroke-3)' : 'var(--stroke)'} strokeDasharray={t === 0 ? undefined : '2 3'} />
      <text x={PL - 4} y={y(t) + 3} className="cot-t" textAnchor="end">{t > 0 ? `+${t}` : t}</text></g>)}
    <text x={PL - 4} y={top - 4} className="cot-t" textAnchor="end">dB</text>
    <text x={W - PR + 3} y={bottom - barH(maxCells) + 3} className="cot-t">{maxCells}</text>
    <text x={W - PR + 3} y={bottom + 3} className="cot-t">0</text>
    {series.map((p, i) => p.status === 'missed'
      ? <rect key={p.date} x={colX(i, n) - cw / 2 + 1} y={bottom - 10} width={cw - 2} height={10} fill={`url(#h${uid})`} stroke="var(--ink-4)" strokeDasharray="2 2" strokeWidth=".6"><title>{shortDate(p.date, true)} · missed pass, no data</title></rect>
      : <rect key={p.date} x={colX(i, n) - cw * 0.32} y={bottom - barH(p.candidate_cells ?? 0)} width={cw * 0.64} height={barH(p.candidate_cells ?? 0)} rx="1" fill={i === index ? 'var(--dmg-severe)' : 'color-mix(in srgb,var(--dmg-severe) 45%,transparent)'} />)}
    {segments(series, pol).map(seg => <polyline key={seg[0].index} fill="none" stroke="var(--ev-observed)" strokeWidth="1.6" strokeLinejoin="round"
      points={seg.map(s => `${colX(s.index, n).toFixed(1)},${y(s.value).toFixed(1)}`).join(' ')} />)}
    {series.map((p, i) => {
      const v = polValue(p, pol); if (v == null) return null
      const suspect = !!p.quality
      return <circle key={p.date} cx={colX(i, n)} cy={y(v)} r={i === index ? 3.4 : suspect ? 2.8 : 2}
        fill={suspect ? 'var(--bg)' : 'var(--ev-observed)'} stroke={suspect ? 'var(--dmg-moderate)' : i === index ? 'var(--ink)' : 'none'} strokeWidth="1.3">
        <title>{`${shortDate(p.date, true)} · ${POL_LABEL[pol]} ${fmtDb(v)}${suspect ? ` · ${p.quality}` : ''}`}</title></circle>
    })}
    {cur && <line x1={colX(index, n)} x2={colX(index, n)} y1={top} y2={bottom} stroke="var(--ink)" strokeWidth="1" strokeDasharray="3 2" opacity=".7" />}
    <line x1={PL} x2={W - PR} y1={bottom} y2={bottom} stroke="var(--stroke-2)" />
    {years.map(({ i, y: yr }) => <text key={yr} x={colX(i, n) - cw / 2} y={CH - 5} className="cot-t">{yr}</text>)}
    {cur && <text x={Math.min(W - PR - 2, Math.max(PL + 40, colX(index, n)))} y={CH - 5} className="cot-t cur" textAnchor="middle">{shortDate(cur.date)}</text>}
    {series.map((p, i) => <rect key={p.date} className={p.status === 'ok' ? 'cot-hit' : undefined} x={colX(i, n) - cw / 2} y={top} width={cw} height={bottom - top}
      fill="transparent" onClick={p.status === 'ok' ? () => onPick(i) : undefined}><title>{shortDate(p.date, true)}{p.status === 'missed' ? ' · missed pass' : ` · ${p.candidate_cells ?? '?'} candidate cells`}</title></rect>)}
  </svg>
}

function BudgetChart({ series, index, onPick }: { series: ChangePoint[]; index: number; onPick: (i: number) => void }) {
  const n = series.length, cw = colW(n), top = 6, bottom = BH - 8
  const max = Math.max(1, ...series.map(p => p.budget_musd?.high ?? 0))
  const y = (v: number) => bottom - (v / max) * (bottom - top)
  const runs: { i: number; low: number; high: number }[][] = []
  let run: { i: number; low: number; high: number }[] = []
  series.forEach((p, i) => {
    if (p.status !== 'ok' || !p.budget_musd) { if (run.length) runs.push(run); run = []; return }
    run.push({ i, ...p.budget_musd })
  })
  if (run.length) runs.push(run)
  const cur = series[index]?.budget_musd
  return <svg className="cot-chart" viewBox={`0 0 ${W} ${BH}`} role="img" aria-label={`Rebuild budget range over time. Current pass: ${budgetText(cur)}`}>
    <line x1={PL} x2={W - PR} y1={bottom} y2={bottom} stroke="var(--stroke-2)" />
    <text x={PL - 4} y={top + 4} className="cot-t" textAnchor="end">${Math.ceil(max)}M</text>
    <text x={PL - 4} y={bottom + 3} className="cot-t" textAnchor="end">0</text>
    {runs.map(r => {
      const pts = [...r.map(p => `${colX(p.i, n).toFixed(1)},${y(p.high).toFixed(1)}`), ...[...r].reverse().map(p => `${colX(p.i, n).toFixed(1)},${y(p.low).toFixed(1)}`)]
      return <g key={r[0].i}>
        <polygon points={pts.join(' ')} fill="color-mix(in srgb,var(--dmg-moderate) 22%,transparent)" stroke="color-mix(in srgb,var(--dmg-moderate) 60%,transparent)" strokeWidth=".8" />
        {r.length === 1 && <line x1={colX(r[0].i, n)} x2={colX(r[0].i, n)} y1={y(r[0].high)} y2={y(r[0].low)} stroke="var(--dmg-moderate)" />}
      </g>
    })}
    <line x1={colX(index, n)} x2={colX(index, n)} y1={top} y2={bottom} stroke="var(--ink)" strokeWidth="1" strokeDasharray="3 2" opacity=".7" />
    {series.map((p, i) => <rect key={p.date} className={p.status === 'ok' ? 'cot-hit' : undefined} x={colX(i, n) - cw / 2} y={top} width={cw} height={bottom - top}
      fill="transparent" onClick={p.status === 'ok' ? () => onPick(i) : undefined}><title>{shortDate(p.date, true)} · {p.status === 'ok' ? budgetText(p.budget_musd) : 'missed pass'}</title></rect>)}
  </svg>
}
