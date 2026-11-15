import { act, renderHook } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, expect, it, vi } from 'vitest'
import type { Pass } from '../../types/map'
import { nextPlayablePassIndex, playablePassIndexes, useTimelinePlayback } from './timeline'

const passes: Pass[] = [
  { id: 'p1', date: '2026-01-01', sensor: 'NISAR', status: 'ok' },
  { id: 'missing', date: '2026-01-13', sensor: 'No acquisition', status: 'missed' },
  { id: 'p2', date: '2026-01-25', sensor: 'NISAR', status: 'ok' },
]

afterEach(() => vi.useRealTimers())

it('keeps missing intervals visible but excludes them from playback', () => {
  expect(playablePassIndexes(passes)).toEqual([0, 2])
  expect(nextPlayablePassIndex(passes, 0)).toBe(2)
  expect(nextPlayablePassIndex(passes, 2)).toBeNull()
})

it('restarts at the first acquisition, advances safely, and stops at the end', () => {
  vi.useFakeTimers()
  const { result, unmount } = renderHook(() => {
    const [index, setIndex] = useState(2)
    return { index, playback: useTimelinePlayback(passes, index, setIndex, 100) }
  })

  act(() => result.current.playback.toggle())
  expect(result.current.index).toBe(0)
  expect(result.current.playback.playing).toBe(true)
  act(() => vi.advanceTimersByTime(100))
  expect(result.current.index).toBe(2)
  act(() => vi.advanceTimersByTime(100))
  expect(result.current.playback.playing).toBe(false)
  unmount()
  expect(vi.getTimerCount()).toBe(0)
})
