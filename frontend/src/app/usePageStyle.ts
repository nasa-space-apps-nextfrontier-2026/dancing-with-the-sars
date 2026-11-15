import { useLayoutEffect } from 'react'

/**
 * Adds a page's stylesheet while the page is mounted and removes it on unmount.
 * The landing page and the dashboard use different designs with overlapping class names,
 * so each route brings only its own CSS (imported with Vite's `?inline`).
 */
export function usePageStyle(css: string, id: string) {
  useLayoutEffect(() => {
    const el = document.createElement('style')
    el.dataset.page = id
    el.textContent = css
    document.head.appendChild(el)
    return () => { el.remove() }
  }, [css, id])
}
