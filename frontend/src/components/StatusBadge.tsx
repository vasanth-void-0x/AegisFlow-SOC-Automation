const STATUS_STYLES: Record<string, { color: string }> = {
  new: { color: 'var(--color-sev-low)' },
  triaging: { color: 'var(--color-signal)' },
  pending_approval: { color: 'var(--color-sev-medium)' },
  contained: { color: 'var(--color-ok)' },
  resolved: { color: 'var(--color-ok)' },
  closed: { color: 'var(--color-ash)' },
  pending: { color: 'var(--color-sev-medium)' },
  approved: { color: 'var(--color-signal)' },
  rejected: { color: 'var(--color-danger)' },
  expired: { color: 'var(--color-ash-dim)' },
  executed: { color: 'var(--color-ok)' },
  rolled_back: { color: 'var(--color-ash)' },
}

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? { color: 'var(--color-ash)' }
  return (
    <span
      className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium font-mono uppercase tracking-wide"
      style={{ color: s.color, borderColor: s.color + '55' }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}
