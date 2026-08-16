import type { Severity } from '../api/types'

const SEVERITY_STYLES: Record<Severity, { color: string; bg: string; label: string }> = {
  low: { color: 'var(--color-sev-low)', bg: 'color-mix(in srgb, var(--color-sev-low) 15%, transparent)', label: 'Low' },
  medium: {
    color: 'var(--color-sev-medium)',
    bg: 'color-mix(in srgb, var(--color-sev-medium) 15%, transparent)',
    label: 'Medium',
  },
  high: {
    color: 'var(--color-sev-high)',
    bg: 'color-mix(in srgb, var(--color-sev-high) 15%, transparent)',
    label: 'High',
  },
  critical: {
    color: 'var(--color-sev-critical)',
    bg: 'color-mix(in srgb, var(--color-sev-critical) 18%, transparent)',
    label: 'Critical',
  },
}

export function severityColor(severity: Severity): string {
  return SEVERITY_STYLES[severity]?.color ?? 'var(--color-ash)'
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const s = SEVERITY_STYLES[severity]
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs font-medium font-mono uppercase tracking-wide"
      style={{ color: s.color, backgroundColor: s.bg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: s.color }} />
      {s.label}
    </span>
  )
}
