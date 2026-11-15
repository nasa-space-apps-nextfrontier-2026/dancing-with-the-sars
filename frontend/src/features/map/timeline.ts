import { useCallback, useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import type { Pass } from '../../types/map'

export function playablePassIndexes(passes: Pass[]): number[] {
  return passes.flatMap((pass, index) => pass.status === 'ok' ? [index] : [])
}

export function nextPlayablePassIndex(passes: Pass[], current: number): number | null {
  return playablePassIndexes(passes).find(index => index > current) ?? null
}

/** Playback visits released acquisitions only. Missing intervals stay visible as timeline markers. */
export function useTimelinePlayback(
  passes: Pass[],
  passIdx: number,
  setPassIdx: Dispatch<SetStateAction<number>>,
  delayMs = 2500,
) {
  const [playing, setPlaying] = useState(false)
  const playable = useMemo(() => playablePassIndexes(passes), [passes])

  useEffect(() => setPlaying(false), [passes])
  useEffect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      setPassIdx(current => {
        const next = nextPlayablePassIndex(passes, current)
        if (next == null) {
          setPlaying(false)
          return current
        }
        return next
      })
    }, delayMs)
    return () => window.clearInterval(timer)
  }, [delayMs, passes, playing, setPassIdx])

  const toggle = useCallback(() => {
    if (playing) {
      setPlaying(false)
      return
    }
    if (playable.length < 2) return
    if (nextPlayablePassIndex(passes, passIdx) == null) setPassIdx(playable[0])
    setPlaying(true)
  }, [passIdx, passes, playable, playing, setPassIdx])

  const select = useCallback((index: number) => {
    setPlaying(false)
    setPassIdx(index)
  }, [setPassIdx])

  return { playing, canPlay: playable.length > 1, toggle, select, stop: () => setPlaying(false) }
}
