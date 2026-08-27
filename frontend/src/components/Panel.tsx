import type { ReactNode } from 'react'

export function Panel({
  title,
  children,
  className = '',
  action,
  subtitle,
}: {
  title?: string
  children: ReactNode
  className?: string
  action?: ReactNode
  subtitle?: string
}) {
  return (
    <section className={`soc-panel ${className}`}>
      {title && (
        <div className="panel-heading">
          <div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
          {action}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  )
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-12 text-center">
      <p className="text-sm font-medium text-[var(--color-fog)]">{title}</p>
      <p className="max-w-xs text-xs text-[var(--color-ash)]">{description}</p>
    </div>
  )
}

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-xs text-[var(--color-ash)]">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-[var(--color-graphite-light)] border-t-[var(--color-signal)]" />
      {label}...
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-3 py-2 text-xs text-[var(--color-danger)]">
      {message}
    </div>
  )
}
