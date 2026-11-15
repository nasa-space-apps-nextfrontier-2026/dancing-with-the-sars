// Stroke icons used across the app (same set as the mockup).
const P: Record<string, string> = {
  incident: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  rank: '<path d="M5 20V10M12 20V4M19 20v-7"/>',
  decide: '<path d="M4 6h10M4 12h16M4 18h7"/><circle cx="17" cy="6" r="2"/><circle cx="14" cy="18" r="2"/>',
  budget: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h4"/>',
  layers: '<path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="m3 13 9 5 9-5"/>',
  legend: '<path d="M5 6h.01M5 12h.01M5 18h.01M9 6h10M9 12h10M9 18h10"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  people: '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.3"/><path d="M16 14.2c2.8.2 5 2.6 5 5.8"/>',
  facility: '<path d="M4 21V8l8-5 8 5v13"/><path d="M10 21v-6h4v6M12 8v4M10 10h4"/>',
  road: '<path d="M8 3 5 21M16 3l3 18M12 4v3M12 10v4M12 17v3"/>',
  power: '<path d="M13 2 5 14h6l-1 8 8-12h-6z"/>',
  fire: '<path d="M12 22c4 0 7-2.8 7-6.8 0-3.6-2.6-5.7-4-8.2-.6 2-1.6 3-3 3.6.4-3.2-1-6.4-3.6-8.6C8.3 6 5 8.6 5 14.6 5 19 8 22 12 22z"/>',
  shelter: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  pin: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/>',
  money: '<path d="M12 3v18M17 7.5c0-1.9-2.2-3-5-3s-5 1.1-5 3 2.2 2.6 5 3.2 5 1.4 5 3.3-2.2 3-5 3-5-1.1-5-3"/>',
  chev: '<path d="m9 6 6 6-6 6"/>',
  check: '<path d="m5 12 4 4 10-10"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  orbit: '<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>',
  plane: '<path d="M12 2 4 20l8-4 8 4z"/>',
}
export type IconName = keyof typeof P
export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" dangerouslySetInnerHTML={{ __html: P[name] }} />
}
export function Logo() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true"><path d="M12 3v6M12 15v6M3 12h6M15 12h6" /><circle cx="12" cy="12" r="2.2" fill="#fff" stroke="none" /></svg>
}

