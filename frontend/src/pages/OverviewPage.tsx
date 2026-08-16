import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Incident } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

export function OverviewPage() {
  const [incidents, setIncidents] = useState<Incident[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listIncidents({ page: 1, page_size: 50 })
      .then((res) => setIncidents(res.items))
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="p-6"><ErrorState message={error} /></div>
  if (!incidents) return <div className="p-6"><LoadingState label="Loading incidents" /></div>

  const bySeverity = { critical: 0, high: 0, medium: 0, low: 0 }
  const openStatuses = new Set(['new', 'triaging', 'pending_approval'])
  let openCount = 0
  incidents.forEach((i) => {
    bySeverity[i.severity]++
    if (openStatuses.has(i.status)) openCount++
  })

  const recent = incidents.slice(0, 8)

  return (
    <div className="p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">SOC Overview</h1>
        <p className="text-sm text-[var(--color-ash)]">Live state derived from the incident queue - no synthetic data.</p>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatCard label="Open Incidents" value={openCount} accent="var(--color-signal)" />
        <StatCard label="Critical" value={bySeverity.critical} accent={severityColor('critical')} />
        <StatCard label="High" value={bySeverity.high} accent={severityColor('high')} />
        <StatCard label="Medium" value={bySeverity.medium} accent={severityColor('medium')} />
        <StatCard label="Low" value={bySeverity.low} accent={severityColor('low')} />
      </div>

      <Panel title="Recent Incidents" action={<Link to="/incidents" className="text-xs text-[var(--color-signal)] hover:underline">View all →</Link>}>
        {recent.length === 0 ? (
          <p className="py-6 text-center text-sm text-[var(--color-ash)]">No incidents ingested yet.</p>
        ) : (
          <div className="divide-y divide-[var(--color-graphite)]">
            {recent.map((inc) => (
              <IncidentRow key={inc.id} incident={inc} />
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="rounded-lg border border-[var(--color-graphite)] bg-[var(--color-steel)] p-4">
      <div className="text-2xl font-mono font-semibold" style={{ color: accent }}>
        {value}
      </div>
      <div className="mt-1 text-xs text-[var(--color-ash)]">{label}</div>
    </div>
  )
}

function IncidentRow({ incident }: { incident: Incident }) {
  return (
    <Link
      to={`/incidents/${incident.id}`}
      className="flex items-center gap-3 py-3 pl-3 -ml-3 pr-2 hover:bg-[var(--color-graphite)]/40 rounded transition-colors"
      style={{ borderLeft: `3px solid ${severityColor(incident.severity)}` }}
    >
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{incident.alert_name}</div>
        <div className="text-xs text-[var(--color-ash-dim)] font-mono">
          {incident.id} · {incident.source} · {new Date(incident.created_at).toLocaleString()}
        </div>
      </div>
      <SeverityBadge severity={incident.severity} />
      <StatusBadge status={incident.status} />
    </Link>
  )
}
