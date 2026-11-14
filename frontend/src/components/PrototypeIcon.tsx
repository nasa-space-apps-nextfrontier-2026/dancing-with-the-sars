export function PrototypeIcon({ name }: { name: string }) {
  return <span className="cv-ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><use href={`/prototype-icons.svg#${name}`} /></svg></span>
}
