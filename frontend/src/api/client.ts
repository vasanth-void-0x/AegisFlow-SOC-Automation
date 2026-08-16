import type {
  EnrichmentResult,
  HealthStatus,
  Incident,
  IncidentListOut,
  IncidentStatus,
  McpToolCallLog,
  ResponseProposal,
  RunbookSearchResult,
  Severity,
  TimelineEvent,
  TriageRecord,
} from './types'

const BASE = '/api/v1'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = path.startsWith('/api/v1') || path === '/health' ? path : `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore parse failure, use statusText */
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<HealthStatus>('/health'),

  listIncidents: (params: {
    page?: number
    page_size?: number
    severity?: Severity
    status?: IncidentStatus
    source?: string
  }) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => v && qs.set(k, String(v)))
    return request<IncidentListOut>(`/incidents?${qs.toString()}`)
  },

  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),

  updateIncidentStatus: (id: string, status: IncidentStatus) =>
    request<Incident>(`/incidents/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),

  enrichIncident: (id: string) => request<EnrichmentResult[]>(`/incidents/${id}/enrichment`),

  enrichIndicator: (indicator_type: string, value: string) =>
    request<EnrichmentResult>(`/enrich?indicator_type=${indicator_type}&value=${encodeURIComponent(value)}`),

  triggerTriage: (id: string) => request<TriageRecord>(`/incidents/${id}/triage`, { method: 'POST' }),

  getTriageHistory: (id: string) => request<TriageRecord[]>(`/incidents/${id}/triage`),

  searchRunbooks: (query: string) =>
    request<RunbookSearchResult>(`/runbooks/search?query=${encodeURIComponent(query)}`),

  listApprovals: (params: { status?: string; incident_id?: string } = {}) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => v && qs.set(k, String(v)))
    return request<ResponseProposal[]>(`/approvals?${qs.toString()}`)
  },

  getApproval: (id: string) => request<ResponseProposal>(`/approvals/${id}`),

  createProposal: (
    incidentId: string,
    body: { action_type: string; target: string; justification: string; proposed_by?: string }
  ) => request<ResponseProposal>(`/incidents/${incidentId}/proposals`, { method: 'POST', body: JSON.stringify(body) }),

  approveProposal: (id: string, approver: string, reason: string) =>
    request<ResponseProposal>(`/approvals/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approver, reason }),
    }),

  rejectProposal: (id: string, approver: string, reason: string) =>
    request<ResponseProposal>(`/approvals/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ approver, reason }),
    }),

  rollbackProposal: (id: string, approver: string, reason: string) =>
    request<ResponseProposal>(`/approvals/${id}/rollback`, {
      method: 'POST',
      body: JSON.stringify({ approver, reason }),
    }),

  getTimeline: (incidentId: string) => request<TimelineEvent[]>(`/incidents/${incidentId}/timeline`),

  getMcpToolCalls: (limit = 50) => request<McpToolCallLog[]>(`/audit/mcp-calls?limit=${limit}`),

  getAuditTimeline: (limit = 100) => request<TimelineEvent[]>(`/audit/timeline?limit=${limit}`),
}

export { ApiError }
