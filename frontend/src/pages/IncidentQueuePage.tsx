import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Incident, IncidentStatus, Severity } from '../api/types'
import { Panel, LoadingState, ErrorState, EmptyState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'
import { useLivePolling } from '../hooks/useLivePolling'

const SEVERITIES: Severity[] = ['critical', 'high', 'medium', 'low']
const STATUSES: IncidentStatus[] = ['new', 'triaging', 'pending_approval', 'contained', 'resolved', 'closed']

export function IncidentQueuePage() {
  const [data, setData] = useState<{ items: Incident[]; total: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState<Severity | ''>('')
  const [status, setStatus] = useState<IncidentStatus | ''>('')
  const [search, setSearch] = useState('')
  const pageSize = 15

  useEffect(() => { setData(null) }, [page, severity, status])
  useLivePolling(() => api
      .listIncidents({
        page,
        page_size: pageSize,
        severity: severity || undefined,
        status: status || undefined,
      })
      .then((result) => { setData(result); setError(null) })
      .catch((e) => setError(e.message)), { intervalMs: 5_000 })

  const filtered = data?.items.filter(
    (i) =>
      !search ||
      i.alert_name.toLowerCase().includes(search.toLowerCase()) ||
      i.id.toLowerCase().includes(search.toLowerCase()) ||
      (i.source_ip ?? '').includes(search)
  )

  return (
    <div className="p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">Incident Queue</h1>
        <p className="text-sm text-[var(--color-ash)]">
          {data ? `${data.total} incident${data.total === 1 ? '' : 's'} total` : 'Loading...'}
        </p>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, ID, or source IP..."
          className="min-w-[220px] flex-1 rounded border border-[var(--color-graphite)] bg-[var(--color-steel)] px-3 py-2 text-sm placeholder:text-[var(--color-ash-dim)] focus:border-[var(--color-signal)]"
        />
        <select
          value={severity}
          onChange={(e) => {
            setSeverity(e.target.value as Severity | '')
            setPage(1)
          }}
          className="rounded border border-[var(--color-graphite)] bg-[var(--color-steel)] px-3 py-2 text-sm"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as IncidentStatus | '')
            setPage(1)
          }}
          className="rounded border border-[var(--color-graphite)] bg-[var(--color-steel)] px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
      </div>

      <Panel>
        {error && !data && <ErrorState message={error} />}
        {!data && !error && <LoadingState label="Loading incidents" />}
        {data && filtered && filtered.length === 0 && (
          <EmptyState title="No incidents match" description="Try clearing filters or search terms." />
        )}
        {filtered && filtered.length > 0 && (
          <div className="-m-4 divide-y divide-[var(--color-graphite)]">
            {filtered.map((inc) => (
              <Link
                key={inc.id}
                to={`/incidents/${inc.id}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--color-graphite)]/40 transition-colors"
                style={{ borderLeft: `3px solid ${severityColor(inc.severity)}` }}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{inc.alert_name}</div>
                  <div className="text-xs text-[var(--color-ash-dim)] font-mono">
                    {inc.id} · {inc.source} {inc.source_ip ? `· ${inc.source_ip}` : ''}
                  </div>
                </div>
                <span className="text-xs text-[var(--color-ash-dim)] font-mono hidden sm:block">
                  {new Date(inc.created_at).toLocaleDateString()}
                </span>
                <SeverityBadge severity={inc.severity} />
                <StatusBadge status={inc.status} />
              </Link>
            ))}
          </div>
        )}
      </Panel>

      {data && data.total > pageSize && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border border-[var(--color-graphite)] px-3 py-1.5 disabled:opacity-40 hover:bg-[var(--color-graphite)]"
          >
            ← Previous
          </button>
          <span className="text-[var(--color-ash)]">
            Page {page} of {Math.ceil(data.total / pageSize)}
          </span>
          <button
            disabled={page >= Math.ceil(data.total / pageSize)}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border border-[var(--color-graphite)] px-3 py-1.5 disabled:opacity-40 hover:bg-[var(--color-graphite)]"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
