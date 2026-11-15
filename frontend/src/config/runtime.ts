type PreviewEnvironment = {
  DEV: boolean
  MODE: string
  VITE_CIVISAR_DEV_PREVIEW?: string
}

/** Local-only preview. Production builds cannot enable it with a VITE value. */
export function isLocalPreview(environment: PreviewEnvironment): boolean {
  return environment.DEV && (
    environment.MODE === 'preview' || environment.VITE_CIVISAR_DEV_PREVIEW === 'true'
  )
}

export const localPreview = isLocalPreview({
  DEV: import.meta.env.DEV,
  MODE: import.meta.env.MODE,
  VITE_CIVISAR_DEV_PREVIEW: import.meta.env.VITE_CIVISAR_DEV_PREVIEW,
})
