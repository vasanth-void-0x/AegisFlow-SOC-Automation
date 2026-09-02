import { useState } from 'react'
import { api } from '../api/client'
import type { McpToolCallLog } from '../api/types'
import { Panel, LoadingState, ErrorState, EmptyState } from '../components/Panel'
import { useLivePolling } from '../hooks/useLivePolling'

export function McpToolHistoryPage() {
  const [logs, setLogs] = useState<McpToolCallLog[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useLivePolling(() => api.getMcpToolCalls(100).then((items) => { setLogs(items); setError(null) }).catch((e) => setError(e.message)), { intervalMs: 5_000 })

  return (
    <div className="p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">MCP Tool History</h1>
        <p className="text-sm text-[var(--color-ash)]">
          Every call made through the BlueOrch MCP security server - allowlisted, timed, and audited.
        </p>
      </header>

      <Panel>
        {error && <ErrorState message={error} />}
        {!logs && !error && <LoadingState label="Loading tool call history" />}
        {logs?.length === 0 && (
          <EmptyState
            title="No MCP tool calls yet"
            description="Calls appear here once an MCP client (e.g. Claude Desktop, or the n8n workflow) invokes a tool."
          />
        )}
        <div className="-m-4 divide-y divide-[var(--color-graphite)]">
          {logs?.map((log) => (
            <div key={log.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm">{log.tool_name}</span>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[var(--color-ash-dim)] font-mono">{log.duration_ms ?? '—'}ms</span>
                  <span
                    className={`rounded px-1.5 py-0.5 font-mono uppercase ${
                      log.success ? 'bg-[var(--color-ok)]/20 text-[var(--color-ok)]' : 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'
                    }`}
                  >
                    {log.success ? 'ok' : 'error'}
                  </span>
                </div>
              </div>
              <div className="mt-1 text-xs text-[var(--color-ash-dim)] font-mono">{new Date(log.created_at).toLocaleString()}</div>
              {log.error && <div className="mt-1 text-xs text-[var(--color-danger)]">{log.error}</div>}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
