import { expect, it } from 'vitest'
import { isLocalPreview } from './runtime'

it('enables preview only in a development build', () => {
  expect(isLocalPreview({ DEV: true, MODE: 'preview' })).toBe(true)
  expect(isLocalPreview({ DEV: true, MODE: 'development', VITE_CIVISAR_DEV_PREVIEW: 'true' })).toBe(true)
  expect(isLocalPreview({ DEV: true, MODE: 'development', VITE_CIVISAR_DEV_PREVIEW: 'false' })).toBe(false)
  expect(isLocalPreview({ DEV: false, MODE: 'preview', VITE_CIVISAR_DEV_PREVIEW: 'true' })).toBe(false)
})
