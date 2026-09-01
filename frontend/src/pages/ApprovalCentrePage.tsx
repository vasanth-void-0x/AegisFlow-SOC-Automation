import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { ResponseProposal } from '../api/types'
import { Panel, LoadingState, ErrorState, EmptyState } from '../components/Panel'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'

export function ApprovalCentrePage() {
  const { user, canOperate } = useAuth()
  const [proposals, setProposals] = useState<ResponseProposal[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('pending')
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = () =>
    api
      .listApprovals(statusFilter ? { status: statusFilter } : {})
      .then(setProposals)
      .catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [statusFilter])

  const act = async (id: string, action: 'approve' | 'reject' | 'rollback') => {
    const reason = window.prompt(`Reason for ${action}?`)
    if (!reason) return
    setBusyId(id)
    try {
      if (action === 'approve') await api.approveProposal(id, user?.username || 'analyst', reason)
      else if (action === 'reject') await api.rejectProposal(id, user?.username || 'analyst', reason)
      else await api.rollbackProposal(id, user?.username || 'analyst', reason)
      await load()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Approval Centre</h1>
          <p className="text-sm text-[var(--color-ash)]">
            AI recommends → human reviews → human approves → system executes. No action runs without approval.
          </p>
        </div>
        <div className="rounded border border-[var(--color-graphite)] bg-[var(--color-steel)] px-3 py-1.5 text-xs font-mono">
          {user?.username} · {user?.role.toUpperCase()}
        </div>
      </header>

      <div className="mb-4 flex gap-2">
        {['pending', 'approved', 'rejected', 'executed', 'expired', 'rolled_back', ''].map((s) => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`rounded px-3 py-1.5 text-xs font-mono uppercase ${
              statusFilter === s ? 'bg-[var(--color-signal)] text-white' : 'border border-[var(--color-graphite)] text-[var(--color-ash)] hover:bg-[var(--color-graphite)]'
            }`}
          >
            {s || 'all'}
          </button>
        ))}
      </div>

      <Panel>
        {error && <ErrorState message={error} />}
        {!proposals && !error && <LoadingState label="Loading proposals" />}
        {proposals?.length === 0 && (
          <EmptyState title="Nothing here" description="No proposals match this filter." />
        )}
        <div className="-m-4 divide-y divide-[var(--color-graphite)]">
          {proposals?.map((p) => (
            <div key={p.id} className="flex items-center gap-4 px-4 py-3">
              <div className="flex-1 min-w-0">
                <div className="text-sm">
                  <span className="font-medium">{p.action_type.replace(/_/g, ' ')}</span>{' '}
                  <span className="text-[var(--color-ash)]">on</span>{' '}
                  <span className="font-mono">{p.target}</span>
                </div>
                <div className="text-xs text-[var(--color-ash-dim)] truncate">{p.justification}</div>
                <Link to={`/incidents/${p.incident_id}`} className="text-xs text-[var(--color-signal)] hover:underline font-mono">
                  {p.incident_id}
                </Link>
              </div>
              <StatusBadge status={p.status} />
              {p.status === 'pending' && canOperate && (
                <div className="flex gap-1.5">
                  <button
                    disabled={busyId === p.id}
                    onClick={() => act(p.id, 'approve')}
                    className="rounded bg-[var(--color-ok)]/20 text-[var(--color-ok)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--color-ok)]/30 disabled:opacity-40"
                  >
                    Approve
                  </button>
                  <button
                    disabled={busyId === p.id}
                    onClick={() => act(p.id, 'reject')}
                    className="rounded bg-[var(--color-danger)]/20 text-[var(--color-danger)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--color-danger)]/30 disabled:opacity-40"
                  >
                    Reject
                  </button>
                </div>
              )}
              {p.status === 'executed' && canOperate && (
                <button
                  disabled={busyId === p.id}
                  onClick={() => act(p.id, 'rollback')}
                  className="rounded border border-[var(--color-graphite)] px-2.5 py-1 text-xs hover:bg-[var(--color-graphite)] disabled:opacity-40"
                >
                  Rollback
                </button>
              )}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
