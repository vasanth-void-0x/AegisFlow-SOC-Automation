import { NavLink, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { HealthStatus } from '../api/types'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/incidents', label: 'Incident Queue' },
  { to: '/approvals', label: 'Approval Centre' },
  { to: '/mcp-tools', label: 'MCP Tool History' },
  { to: '/audit', label: 'Audit Log' },
  { to: '/health', label: 'System Health' },
]

export function AppShell() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [healthError, setHealthError] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    const poll = () => {
      api
        .health()
        .then((h) => !cancelled && (setHealth(h), setHealthError(false)))
        .catch(() => !cancelled && setHealthError(true))
    }
    poll()
    const interval = setInterval(poll, 15000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const sidebarContent = (
    <>
      <div className="flex items-center gap-2 border-b border-[var(--color-graphite)] px-5 py-5">
        <div className="h-2 w-2 rounded-full bg-[var(--color-signal)] shadow-[0_0_8px_var(--color-signal)]" />
        <div>
          <div className="font-mono text-sm font-semibold tracking-tight">AegisFlow</div>
          <div className="text-[10px] uppercase tracking-widest text-[var(--color-ash-dim)]">SOC Orchestrator</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setMobileNavOpen(false)}
            className={({ isActive }) =>
              `rounded px-3 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-[var(--color-signal-glow)] text-[var(--color-fog)] font-medium'
                  : 'text-[var(--color-ash)] hover:bg-[var(--color-graphite)] hover:text-[var(--color-fog)]'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-[var(--color-graphite)] px-4 py-3">
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              healthError ? 'bg-[var(--color-danger)]' : health?.status === 'ok' ? 'bg-[var(--color-ok)]' : 'bg-[var(--color-warn)]'
            }`}
          />
          <span className="text-[var(--color-ash)]">
            {healthError ? 'Backend unreachable' : health ? `${health.environment} · demo=${health.demo_mode}` : 'Checking...'}
          </span>
        </div>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen bg-[var(--color-obsidian)] text-[var(--color-fog)]">
      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-30 flex items-center gap-3 border-b border-[var(--color-graphite)] bg-[var(--color-steel)] px-4 py-3 md:hidden">
        <button
          onClick={() => setMobileNavOpen(true)}
          aria-label="Open navigation menu"
          className="rounded p-1.5 text-[var(--color-fog)] hover:bg-[var(--color-graphite)]"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M3 5h14M3 10h14M3 15h14" strokeLinecap="round" />
          </svg>
        </button>
        <span className="font-mono text-sm font-semibold">AegisFlow</span>
      </div>

      {/* Mobile drawer overlay */}
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - fixed drawer on mobile, static column on desktop */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-60 shrink-0 flex-col border-r border-[var(--color-graphite)] bg-[var(--color-steel)] transition-transform duration-200 md:static md:translate-x-0 ${
          mobileNavOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>

      <main className="flex-1 overflow-auto pt-14 md:pt-0">
        <Outlet />
      </main>
    </div>
  )
}
