export type Severity = 'low' | 'medium' | 'high' | 'critical'
export type IncidentStatus =
  | 'new'
  | 'triaging'
  | 'pending_approval'
  | 'contained'
  | 'resolved'
  | 'closed'

export interface Indicator {
  type: string
  value: string
}

export interface Incident {
  id: string
  fingerprint: string
  source: string
  alert_name: string
  severity: Severity
  description: string
  source_ip: string | null
  destination_ip: string | null
  hostname: string | null
  username: string | null
  event_time: string
  raw_event: Record<string, unknown>
  indicators: Indicator[]
  status: IncidentStatus
  created_at: string
  updated_at: string
}

export interface IncidentListOut {
  items: Incident[]
  total: number
  page: number
  page_size: number
}

export interface EnrichmentResult {
  indicator_type: string
  value: string
  is_public: boolean | null
  source: 'live' | 'cached' | 'demo'
  provider: string
  virustotal: {
    malicious: number
    suspicious: number
    harmless: number
    undetected: number
    total_engines: number
    reputation: number | null
  } | null
  geo: {
    country: string | null
    city: string | null
    asn: string | null
    org: string | null
  } | null
  mitre_techniques: { technique_id: string; name: string; tactic: string }[]
  error: string | null
}

export interface TriageResultData {
  classification: 'true_positive' | 'false_positive' | 'benign' | 'needs_more_info'
  confidence: number
  recommended_severity: string
  summary: string
  evidence: string[]
  mitre_techniques: string[]
  recommended_actions: string[]
  requires_human_approval: boolean
}

export interface TriageRecord {
  id: string
  incident_id: string
  model_name: string
  prompt_version: string
  result: TriageResultData | null
  is_fallback: boolean
  raw_response: string | null
  error: string | null
  token_usage_prompt: number | null
  token_usage_completion: number | null
  latency_ms: number | null
  created_at: string
}

export interface ResponseProposal {
  id: string
  incident_id: string
  action_type: 'block_ip' | 'isolate_host' | 'disable_account' | 'rollback'
  target: string
  justification: string
  proposed_by: string
  status: 'pending' | 'approved' | 'rejected' | 'expired' | 'executed' | 'rolled_back'
  approver: string | null
  approval_reason: string | null
  decided_at: string | null
  execution_result: Record<string, unknown> | null
  expires_at: string | null
  created_at: string
}

export interface TimelineEvent {
  id: string
  incident_id: string
  event_type: string
  description: string
  actor: string
  event_metadata: Record<string, unknown>
  created_at: string
}

export interface RunbookSearchResult {
  found: boolean
  provider?: string
  results: {
    text: string
    metadata: { title: string; heading: string; source_file: string; category: string }
    score: number
    citation: string
  }[]
  message?: string
}

export interface McpToolCallLog {
  id: string
  tool_name: string
  arguments: Record<string, unknown>
  result_summary: Record<string, unknown> | null
  success: boolean
  error: string | null
  duration_ms: number | null
  created_at: string
}

export interface HealthStatus {
  status: string
  app: string
  environment: string
  demo_mode: boolean
  database: string
}

export type SiemProvider = 'splunk' | 'wazuh'

export interface SiemConnectInput {
  provider: SiemProvider
  base_url: string
  token?: string
  username?: string
  password?: string
  index_name?: string
  verify_ssl: boolean
}

export interface SiemConnection {
  id: string
  provider: SiemProvider
  base_url: string
  index_name: string | null
  verify_ssl: boolean
  enabled: boolean
  connected: boolean
  last_error: string | null
  last_checked_at: string | null
  last_synced_at: string | null
}

export interface SiemTestResult {
  provider: SiemProvider
  connected: boolean
  message: string
}

export interface SiemSyncResult {
  provider: SiemProvider
  fetched: number
  created: number
  duplicates: number
  failed: number
  synced_at: string
}

export interface DashboardKpis {
  connection_status: 'connected' | 'disconnected' | 'not_configured'
  provider: SiemProvider | null
  last_synced_at: string | null
  total_alerts: number
  critical_alerts: number
  high_alerts: number
  active_incidents: number
  contained_threats: number
}

export interface LogAgentStatus {
  id: string
  name: string
  platform: 'windows' | 'linux'
  profile: 'security' | 'system' | 'full'
  hostname: string | null
  agent_version: string | null
  status: 'online' | 'offline'
  last_seen_at: string | null
  events_received: number
  created_at: string
}

export interface LogAgentRegistration {
  id: string
  name: string
  platform: string
  profile: string
  api_key: string
  ingest_path: string
  heartbeat_path: string
}
