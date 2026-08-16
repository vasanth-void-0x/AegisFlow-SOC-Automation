import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { HealthStatus } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'

export function SystemHealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const check = () => {
    api
      .health()
      .then((h) => {
        setHealth(h)
        setError(null)
        setLastChecked(new Date())
      })
      .catch((e) => {
        setError(e.message)
        setLastChecked(new Date())
      })
  }

  useEffect(() => {
    check()
    const interval = setInterval(check, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">System Health</h1>
        <p className="text-sm text-[var(--color-ash)]">Live backend status - polled every 10 seconds.</p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Backend API">
          {error && <ErrorState message={`Unreachable: ${error}`} />}
          {!error && !health && <LoadingState label="Checking" />}
          {health && (
            <dl className="space-y-2 text-sm">
              <Row label="Status" value={health.status} accent={health.status === 'ok' ? 'var(--color-ok)' : 'var(--color-danger)'} />
              <Row label="Application" value={health.app} />
              <Row label="Environment" value={health.environment} />
              <Row label="Demo Mode" value={String(health.demo_mode)} accent={health.demo_mode ? 'var(--color-sev-medium)' : 'var(--color-ok)'} />
              <Row label="Database" value={health.database} accent={health.database === 'ok' ? 'var(--color-ok)' : 'var(--color-danger)'} />
            </dl>
          )}
        </Panel>

        <Panel title="Poll Info">
          <dl className="space-y-2 text-sm">
            <Row label="Last checked" value={lastChecked ? lastChecked.toLocaleTimeString() : '—'} />
            <Row label="Polling interval" value="10s" />
          </dl>
          <p className="mt-3 text-xs text-[var(--color-ash-dim)]">
            This page reflects the real /health endpoint response - it is not simulated.
          </p>
        </Panel>
      </div>
    </div>
  )
}

function Row({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-[var(--color-ash)]">{label}</dt>
      <dd className="font-mono" style={accent ? { color: accent } : undefined}>
        {value}
      </dd>
    </div>
  )
}
