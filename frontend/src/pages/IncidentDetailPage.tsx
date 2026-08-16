import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import type {
  EnrichmentResult,
  Incident,
  ResponseProposal,
  TimelineEvent,
  TriageRecord,
} from '../api/types'
import { Panel, LoadingState, ErrorState, EmptyState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

const TABS = ['Overview', 'AI Investigation', 'IOC Enrichment', 'Timeline', 'Response'] as const
type Tab = (typeof TABS)[number]

export function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('Overview')

  const reload = () => {
    if (!id) return
    api.getIncident(id).then(setIncident).catch((e) => setError(e.message))
  }

  useEffect(() => {
    reload()
  }, [id])

  if (error) return <div className="p-6"><ErrorState message={error} /></div>
  if (!incident) return <div className="p-6"><LoadingState label="Loading incident" /></div>

  return (
    <div className="p-6">
      <header className="mb-4" style={{ borderLeft: `4px solid ${severityColor(incident.severity)}`, paddingLeft: 16 }}>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">{incident.alert_name}</h1>
          <SeverityBadge severity={incident.severity} />
          <StatusBadge status={incident.status} />
        </div>
        <p className="mt-1 text-xs text-[var(--color-ash-dim)] font-mono">
          {incident.id} · {incident.source} · created {new Date(incident.created_at).toLocaleString()}
        </p>
      </header>

      <div className="mb-4 flex gap-1 border-b border-[var(--color-graphite)]">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm border-b-2 transition-colors ${
              tab === t
                ? 'border-[var(--color-signal)] text-[var(--color-fog)]'
                : 'border-transparent text-[var(--color-ash)] hover:text-[var(--color-fog)]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Overview' && <OverviewTab incident={incident} />}
      {tab === 'AI Investigation' && <AiInvestigationTab incident={incident} />}
      {tab === 'IOC Enrichment' && <EnrichmentTab incident={incident} />}
      {tab === 'Timeline' && <TimelineTab incidentId={incident.id} />}
      {tab === 'Response' && <ResponseTab incident={incident} onChange={reload} />}
    </div>
  )
}

function OverviewTab({ incident }: { incident: Incident }) {
  const fields: [string, string | null][] = [
    ['Description', incident.description || '—'],
    ['Source IP', incident.source_ip],
    ['Destination IP', incident.destination_ip],
    ['Hostname', incident.hostname],
    ['Username', incident.username],
    ['Event Time', new Date(incident.event_time).toLocaleString()],
    ['Fingerprint', incident.fingerprint],
  ]
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Panel title="Alert Details">
        <dl className="space-y-2 text-sm">
          {fields.map(([label, value]) => (
            <div key={label} className="flex justify-between gap-4">
              <dt className="text-[var(--color-ash)]">{label}</dt>
              <dd className="font-mono text-right break-all">{value || '—'}</dd>
            </div>
          ))}
        </dl>
      </Panel>
      <Panel title="Indicators of Compromise">
        {incident.indicators.length === 0 ? (
          <EmptyState title="No indicators" description="This alert did not include any IOCs." />
        ) : (
          <ul className="space-y-1.5 text-sm font-mono">
            {incident.indicators.map((ind, i) => (
              <li key={i} className="flex justify-between rounded bg-[var(--color-obsidian)] px-2 py-1.5">
                <span className="text-[var(--color-ash)] uppercase text-xs self-center">{ind.type}</span>
                <span>{ind.value}</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}

function AiInvestigationTab({ incident }: { incident: Incident }) {
  const [history, setHistory] = useState<TriageRecord[] | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = () => api.getTriageHistory(incident.id).then(setHistory).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [incident.id])

  const runTriage = async () => {
    setRunning(true)
    setError(null)
    try {
      await api.triggerTriage(incident.id)
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Panel
      title="AI Triage History"
      action={
        <button
          onClick={runTriage}
          disabled={running}
          className="rounded bg-[var(--color-signal)] px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50 hover:bg-[var(--color-signal-dim)]"
        >
          {running ? 'Running triage...' : 'Run AI Triage'}
        </button>
      }
    >
      {error && <ErrorState message={error} />}
      {!history && !error && <LoadingState label="Loading triage history" />}
      {history && history.length === 0 && (
        <EmptyState title="No triage runs yet" description="Click 'Run AI Triage' to generate a structured assessment." />
      )}
      <div className="space-y-4">
        {history?.map((record) => (
          <div key={record.id} className="rounded border border-[var(--color-graphite)] p-3">
            <div className="mb-2 flex items-center justify-between text-xs text-[var(--color-ash-dim)] font-mono">
              <span>
                {record.model_name} · {new Date(record.created_at).toLocaleString()}
                {record.is_fallback && (
                  <span className="ml-2 rounded bg-[var(--color-warn)]/20 px-1.5 py-0.5 text-[var(--color-warn)]">
                    FALLBACK MODE
                  </span>
                )}
              </span>
              {record.latency_ms != null && <span>{record.latency_ms}ms</span>}
            </div>
            {record.result ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="rounded bg-[var(--color-graphite)] px-2 py-0.5 text-xs font-mono uppercase">
                    {record.result.classification.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-[var(--color-ash)]">
                    confidence {(record.result.confidence * 100).toFixed(0)}%
                  </span>
                  {record.result.requires_human_approval && (
                    <span className="rounded border border-[var(--color-sev-medium)] px-1.5 py-0.5 text-[10px] text-[var(--color-sev-medium)]">
                      REQUIRES APPROVAL
                    </span>
                  )}
                </div>
                <p className="text-[var(--color-fog)]">{record.result.summary}</p>
                {record.result.evidence.length > 0 && (
                  <div>
                    <div className="text-xs text-[var(--color-ash)] mb-1">Evidence</div>
                    <ul className="list-disc list-inside text-xs text-[var(--color-ash)] space-y-0.5">
                      {record.result.evidence.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {record.result.recommended_actions.length > 0 && (
                  <div>
                    <div className="text-xs text-[var(--color-ash)] mb-1">Recommended Actions</div>
                    <ul className="list-disc list-inside text-xs space-y-0.5">
                      {record.result.recommended_actions.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <ErrorState message={record.error ?? 'Triage failed with no result'} />
            )}
          </div>
        ))}
      </div>
    </Panel>
  )
}

function EnrichmentTab({ incident }: { incident: Incident }) {
  const [results, setResults] = useState<EnrichmentResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      setResults(await api.enrichIncident(incident.id))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident.id])

  return (
    <Panel
      title="IOC Enrichment"
      action={
        <button
          onClick={run}
          disabled={loading}
          className="rounded border border-[var(--color-graphite)] px-3 py-1.5 text-xs hover:bg-[var(--color-graphite)] disabled:opacity-50"
        >
          {loading ? 'Enriching...' : 'Re-run Enrichment'}
        </button>
      }
    >
      {error && <ErrorState message={error} />}
      {loading && !results && <LoadingState label="Enriching indicators" />}
      {results && results.length === 0 && (
        <EmptyState title="No indicators to enrich" description="This incident has no attached IOCs." />
      )}
      <div className="space-y-3">
        {results?.map((r, i) => (
          <div key={i} className="rounded border border-[var(--color-graphite)] p-3 text-sm">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono">
                <span className="text-[var(--color-ash)] uppercase text-xs mr-2">{r.indicator_type}</span>
                {r.value}
              </span>
              <span
                className={`text-[10px] uppercase rounded px-1.5 py-0.5 font-mono ${
                  r.source === 'live'
                    ? 'bg-[var(--color-ok)]/20 text-[var(--color-ok)]'
                    : r.source === 'cached'
                      ? 'bg-[var(--color-signal)]/20 text-[var(--color-signal)]'
                      : 'bg-[var(--color-ash)]/20 text-[var(--color-ash)]'
                }`}
              >
                {r.source}
              </span>
            </div>
            {r.virustotal && (
              <div className="flex gap-4 text-xs text-[var(--color-ash)] mb-1">
                <span>
                  malicious: <span className="text-[var(--color-danger)]">{r.virustotal.malicious}</span>
                </span>
                <span>suspicious: {r.virustotal.suspicious}</span>
                <span>harmless: {r.virustotal.harmless}</span>
                <span>engines: {r.virustotal.total_engines}</span>
              </div>
            )}
            {r.geo && (
              <div className="text-xs text-[var(--color-ash)]">
                {r.geo.country && `${r.geo.country} · `}
                {r.geo.org}
              </div>
            )}
            {r.mitre_techniques.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {r.mitre_techniques.map((t) => (
                  <span key={t.technique_id} className="rounded bg-[var(--color-signal-glow)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--color-signal)]">
                    {t.technique_id} · {t.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Panel>
  )
}

function TimelineTab({ incidentId }: { incidentId: string }) {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getTimeline(incidentId).then(setEvents).catch((e) => setError(e.message))
  }, [incidentId])

  if (error) return <ErrorState message={error} />
  if (!events) return <LoadingState label="Loading timeline" />

  return (
    <Panel title="Incident Timeline (Immutable)">
      {events.length === 0 ? (
        <EmptyState title="No events yet" description="Timeline events appear as this incident is processed." />
      ) : (
        <ol className="relative border-l border-[var(--color-graphite)] pl-4 space-y-4">
          {events.map((e) => (
            <li key={e.id} className="relative">
              <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-[var(--color-signal)]" />
              <div className="text-xs text-[var(--color-ash-dim)] font-mono">
                {new Date(e.created_at).toLocaleString()} · {e.actor}
              </div>
              <div className="text-sm">{e.description}</div>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  )
}

function ResponseTab({ incident, onChange }: { incident: Incident; onChange: () => void }) {
  const [proposals, setProposals] = useState<ResponseProposal[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ action_type: 'block_ip', target: incident.source_ip ?? '', justification: '' })
  const [submitting, setSubmitting] = useState(false)

  const load = () => api.listApprovals({ incident_id: incident.id }).then(setProposals).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [incident.id])

  const submit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await api.createProposal(incident.id, { ...form, proposed_by: 'analyst' })
      setForm({ ...form, justification: '' })
      await load()
      onChange()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <Panel title="Propose Response Action">
        <div className="grid gap-3 sm:grid-cols-3">
          <select
            value={form.action_type}
            onChange={(e) => setForm({ ...form, action_type: e.target.value })}
            className="rounded border border-[var(--color-graphite)] bg-[var(--color-obsidian)] px-3 py-2 text-sm"
          >
            <option value="block_ip">Block IP</option>
            <option value="isolate_host">Isolate Host</option>
            <option value="disable_account">Disable Account</option>
          </select>
          <input
            value={form.target}
            onChange={(e) => setForm({ ...form, target: e.target.value })}
            placeholder="Target (IP/host/account)"
            className="rounded border border-[var(--color-graphite)] bg-[var(--color-obsidian)] px-3 py-2 text-sm"
          />
          <button
            onClick={submit}
            disabled={submitting || !form.target || form.justification.length < 10}
            className="rounded bg-[var(--color-signal)] px-3 py-2 text-sm font-medium text-white disabled:opacity-40 hover:bg-[var(--color-signal-dim)]"
          >
            {submitting ? 'Creating...' : 'Create Proposal'}
          </button>
        </div>
        <textarea
          value={form.justification}
          onChange={(e) => setForm({ ...form, justification: e.target.value })}
          placeholder="Justification (min 10 characters) - this proposal will require human approval before anything executes"
          className="mt-3 w-full rounded border border-[var(--color-graphite)] bg-[var(--color-obsidian)] px-3 py-2 text-sm"
          rows={2}
        />
        {error && <div className="mt-2"><ErrorState message={error} /></div>}
      </Panel>

      <Panel title="Response Proposals for this Incident">
        {!proposals && <LoadingState label="Loading proposals" />}
        {proposals?.length === 0 && <EmptyState title="No proposals yet" description="Create one above, or via MCP / n8n." />}
        <div className="space-y-2">
          {proposals?.map((p) => (
            <div key={p.id} className="flex items-center justify-between rounded border border-[var(--color-graphite)] p-3 text-sm">
              <div>
                <div className="font-mono text-xs text-[var(--color-ash-dim)]">{p.id}</div>
                <div>
                  {p.action_type.replace(/_/g, ' ')} → <span className="font-mono">{p.target}</span>
                </div>
              </div>
              <StatusBadge status={p.status} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
