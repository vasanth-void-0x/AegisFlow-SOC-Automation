import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { TimelineEvent } from '../api/types'
import { Panel, LoadingState, ErrorState, EmptyState } from '../components/Panel'

export function AuditLogPage() {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getAuditTimeline(100)
      .then(setEvents)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">Audit Log</h1>
        <p className="text-sm text-[var(--color-ash)]">Immutable, append-only feed of every event across every incident.</p>
      </header>

      <Panel>
        {error && <ErrorState message={error} />}
        {!events && !error && <LoadingState label="Loading audit log" />}
        {events?.length === 0 && <EmptyState title="Empty" description="No events recorded yet." />}
        <div className="-m-4 divide-y divide-[var(--color-graphite)]">
          {events?.map((e) => (
            <div key={e.id} className="flex items-start justify-between gap-4 px-4 py-3">
              <div>
                <div className="text-sm">{e.description}</div>
                <div className="mt-0.5 text-xs text-[var(--color-ash-dim)] font-mono">
                  {e.actor} · {new Date(e.created_at).toLocaleString()} ·{' '}
                  <Link to={`/incidents/${e.incident_id}`} className="text-[var(--color-signal)] hover:underline">
                    {e.incident_id}
                  </Link>
                </div>
              </div>
              <span className="shrink-0 rounded bg-[var(--color-graphite)] px-2 py-0.5 text-[10px] font-mono uppercase text-[var(--color-ash)]">
                {e.event_type.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
