import { useEffect, useRef } from 'react'

type PollOptions = { enabled?: boolean; intervalMs?: number; runImmediately?: boolean }

export function useLivePolling(callback: () => void | Promise<void>, { enabled = true, intervalMs = 10_000, runImmediately = true }: PollOptions = {}) {
  const callbackRef = useRef(callback)
  callbackRef.current = callback

  useEffect(() => {
    if (!enabled) return
    let active = true
    let inFlight = false
    const poll = async () => {
      if (!active || inFlight || document.visibilityState === 'hidden') return
      inFlight = true
      try { await callbackRef.current() } finally { inFlight = false }
    }
    const refreshOnFocus = () => void poll()
    if (runImmediately) void poll()
    const timer = window.setInterval(() => void poll(), intervalMs)
    window.addEventListener('focus', refreshOnFocus)
    document.addEventListener('visibilitychange', refreshOnFocus)
    return () => {
      active = false
      window.clearInterval(timer)
      window.removeEventListener('focus', refreshOnFocus)
      document.removeEventListener('visibilitychange', refreshOnFocus)
    }
  }, [enabled, intervalMs, runImmediately])
}
