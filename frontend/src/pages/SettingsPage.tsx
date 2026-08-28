import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import type { SiemConnectInput, SiemConnection, SiemProvider } from '../api/types'
import { LoadingState } from '../components/Panel'

const INITIAL: SiemConnectInput = {
  provider: 'splunk', base_url: '', token: '', username: '', password: '', index_name: '', verify_ssl: true,
}
const PROVIDER_LOGOS = { splunk: 'data:image/png;base64,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', wazuh: 'data:image/png;base64,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' } as const

export function SettingsPage() {
  const [sourceMode, setSourceMode] = useState<'siem' | 'direct'>('siem')
  const [form, setForm] = useState<SiemConnectInput>(INITIAL)
  const [connections, setConnections] = useState<SiemConnection[] | null>(null)
  const [busy, setBusy] = useState<'test' | 'connect' | 'sync' | 'disconnect' | null>(null)
  const [notice, setNotice] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)

  const loadStatus = useCallback(() => api.getSiemStatus().then(setConnections).catch((error: Error) => setNotice({ kind: 'error', text: error.message })), [])
  useEffect(() => { void loadStatus() }, [loadStatus])

  const provider = form.provider
  const connected = connections?.find(item => item.provider === provider)
  const payload = (): SiemConnectInput => provider === 'splunk'
    ? { provider, base_url: form.base_url, token: form.token, index_name: form.index_name || 'security', verify_ssl: form.verify_ssl }
    : { provider, base_url: form.base_url, username: form.username, password: form.password, index_name: form.index_name || 'wazuh-alerts-*', verify_ssl: form.verify_ssl }

  const run = async (action: 'test' | 'connect') => {
    setBusy(action); setNotice(null)
    try {
      if (action === 'test') {
        const result = await api.testSiem(payload()); setNotice({ kind: 'ok', text: result.message })
      } else {
        await api.connectSiem(payload()); setNotice({ kind: 'ok', text: `${provider === 'splunk' ? 'Splunk' : 'Wazuh'} connected. Real alert ingestion is ready.` }); await loadStatus()
      }
    } catch (error) {
      const text = error instanceof ApiError ? error.message : 'Unable to reach the SIEM'; setNotice({ kind: 'error', text })
    } finally { setBusy(null) }
  }

  const submit = (event: FormEvent) => { event.preventDefault(); void run('connect') }
  const sync = async () => {
    setBusy('sync'); setNotice(null)
    try { const r = await api.syncSiem(provider); setNotice({ kind: 'ok', text: `Sync complete: ${r.created} new, ${r.duplicates} duplicates, ${r.failed} failed.` }); await loadStatus() }
    catch (error) { setNotice({ kind: 'error', text: error instanceof Error ? error.message : 'Sync failed' }) }
    finally { setBusy(null) }
  }
  const disconnect = async () => {
    setBusy('disconnect'); setNotice(null)
    try { await api.disconnectSiem(provider); setNotice({ kind: 'ok', text: `${provider} disconnected and stored credentials removed.` }); await loadStatus() }
    catch (error) { setNotice({ kind: 'error', text: error instanceof Error ? error.message : 'Disconnect failed' }) }
    finally { setBusy(null) }
  }

  if (!connections) return <div className="page-pad"><LoadingState label="Loading SIEM configuration" /></div>
  return <div className="page-pad settings-page">
    <section className="page-intro"><div><span className="section-kicker">REAL TELEMETRY · TWO INGESTION MODES · NO DEMO DATA</span><h1>Security Data Sources</h1><p>Connect an existing SIEM or send endpoint and infrastructure logs directly to AegisFlow.</p></div></section>
    <nav className="source-mode-switch" aria-label="Log ingestion mode">
      <button type="button" className={sourceMode === 'siem' ? 'active' : ''} onClick={() => { setSourceMode('siem'); setNotice(null) }}><i>01</i><span><b>SIEM Integration</b><small>Splunk · Wazuh</small></span><em>{sourceMode === 'siem' ? '✓ SELECTED' : connections.some(item => item.connected) ? 'ONLINE' : 'OFFLINE'}</em></button>
      <button type="button" className={sourceMode === 'direct' ? 'active' : ''} onClick={() => { setSourceMode('direct'); setNotice(null) }}><i>02</i><span><b>Direct Log Source</b><small>24/7 Agent · Webhook · Syslog · File</small></span><em>{sourceMode === 'direct' ? '✓ SELECTED' : 'SETUP'}</em></button>
    </nav>
    {sourceMode === 'siem' ? <div className="siem-layout">
      <section className="siem-card">
        <div className="siem-card-head"><div><span className="section-kicker">DATA SOURCE</span><h2>Configure SIEM</h2></div><ConnectionSignal connection={connected} /></div>
        <div className="provider-tabs" role="tablist" aria-label="SIEM provider">
          {(['splunk','wazuh'] as SiemProvider[]).map(item => <button type="button" role="tab" aria-selected={provider === item} className={provider === item ? 'active' : ''} key={item} onClick={() => { setForm({ ...INITIAL, provider: item, index_name: item === 'splunk' ? 'security' : 'wazuh-alerts-*' }); setNotice(null) }}><img className={`provider-sticker ${item}`} src={PROVIDER_LOGOS[item]} alt={item === 'splunk' ? 'Splunk logo' : 'Wazuh logo'} /><b>{item === 'splunk' ? 'Splunk' : 'Wazuh'}</b><small>{item === 'splunk' ? 'Management API · 8089' : 'Indexer API · 9200'}</small></button>)}
        </div>
        <form onSubmit={submit} className="siem-form">
          <label><span>{provider === 'splunk' ? 'Splunk API URL' : 'Wazuh Indexer URL'}</span><input required type="url" value={form.base_url} onChange={e => setForm({...form, base_url:e.target.value})} placeholder={provider === 'splunk' ? 'https://splunk.company.local:8089' : 'https://wazuh-indexer.company.local:9200'} /></label>
          {provider === 'splunk' ? <label><span>API Token</span><input required type="password" autoComplete="off" value={form.token ?? ''} onChange={e => setForm({...form, token:e.target.value})} placeholder="Enter Splunk bearer token" /></label> : <div className="form-split"><label><span>Username</span><input required autoComplete="username" value={form.username ?? ''} onChange={e => setForm({...form, username:e.target.value})} /></label><label><span>Password</span><input required type="password" autoComplete="current-password" value={form.password ?? ''} onChange={e => setForm({...form, password:e.target.value})} /></label></div>}
          <label><span>{provider === 'splunk' ? 'Index' : 'Alert Index Pattern'}</span><input required value={form.index_name ?? ''} onChange={e => setForm({...form, index_name:e.target.value})} placeholder={provider === 'splunk' ? 'security' : 'wazuh-alerts-*'} /></label>
          <label className="ssl-toggle"><input type="checkbox" checked={form.verify_ssl} onChange={e => setForm({...form, verify_ssl:e.target.checked})} /><i/><span><b>Verify TLS certificate</b><small>Recommended for production SIEM connections</small></span></label>
          {notice ? <div role="status" className={`siem-notice ${notice.kind}`}>{notice.kind === 'ok' ? '✓' : '!'}<span>{notice.text}</span></div> : null}
          <div className="siem-actions"><button type="button" className="secondary-action" disabled={busy !== null} onClick={() => void run('test')}>{busy === 'test' ? 'Testing…' : 'Test Connection'}</button><button className="primary-action" disabled={busy !== null}>{busy === 'connect' ? 'Connecting…' : connected ? 'Update Connection' : 'Connect SIEM'}</button></div>
        </form>
      </section>
      <aside className="connection-summary">
        <div className="summary-signal"><span className={connected?.connected ? 'on' : ''}/><div><small>CONNECTION SIGNAL</small><b>{connected?.connected ? 'SIEM ONLINE' : 'SIEM OFFLINE'}</b><p>{connected ? `${connected.provider.toUpperCase()} · ${connected.base_url}` : 'No real telemetry source connected'}</p></div></div>
        <dl><div><dt>Provider</dt><dd>{connected?.provider.toUpperCase() ?? '—'}</dd></div><div><dt>Index</dt><dd>{connected?.index_name ?? '—'}</dd></div><div><dt>Last checked</dt><dd>{formatTime(connected?.last_checked_at)}</dd></div><div><dt>Last synced</dt><dd>{formatTime(connected?.last_synced_at)}</dd></div><div><dt>TLS verification</dt><dd>{connected ? (connected.verify_ssl ? 'Enabled' : 'Disabled') : '—'}</dd></div></dl>
        {connected?.last_error ? <div className="connection-error">{connected.last_error}</div> : null}
        <button className="sync-action" disabled={!connected || busy !== null} onClick={() => void sync()}>{busy === 'sync' ? 'Synchronizing…' : 'Sync Alerts Now'}</button>
        <button className="disconnect-action" disabled={!connected || busy !== null} onClick={() => void disconnect()}>{busy === 'disconnect' ? 'Disconnecting…' : 'Disconnect & Remove Credentials'}</button>
        <p className="credential-note">Credentials are encrypted by the backend and never returned to this browser.</p>
      </aside>
    </div> : <DirectLogSetup />}
  </div>
}

type DirectMethod = 'agent' | 'webhook' | 'syslog' | 'file'

function DirectLogSetup() {
  const [method, setMethod] = useState<DirectMethod>('agent')
  const [sourceName, setSourceName] = useState('')
  const [directNotice, setDirectNotice] = useState(false)
  const methods: { id: DirectMethod; icon: string; title: string; detail: string }[] = [
    { id: 'agent', icon: '24', title: '24/7 Live Agent', detail: 'Windows · Linux devices' },
    { id: 'webhook', icon: '{}', title: 'JSON Webhook', detail: 'Apps · EDR · Cloud alerts' },
    { id: 'syslog', icon: '>>', title: 'Syslog Forwarder', detail: 'Firewall · IDS · Servers' },
    { id: 'file', icon: '↑', title: 'Secure File', detail: '.log · .json · .csv · .evtx' },
  ]

  return <div className="direct-log-layout">
    <section className="siem-card direct-log-card">
      <div className="siem-card-head"><div><span className="section-kicker">DIRECT INGESTION</span><h2>24/7 Direct Log Monitoring</h2><p>Install a lightweight collector once. AegisFlow receives live logs continuously—even when this dashboard is closed.</p></div><div className="connection-pill direct-ready"><span/>FRONTEND READY</div></div>
      <div className="direct-methods" role="tablist" aria-label="Direct log method">
        {methods.map(item => <button type="button" role="tab" aria-selected={method === item.id} className={method === item.id ? 'active' : ''} key={item.id} onClick={() => { setMethod(item.id); setDirectNotice(false) }}><i>{item.icon}</i><b>{item.title}</b><small>{item.detail}</small></button>)}
      </div>
      <div className="direct-config">
        <label><span>SOURCE NAME</span><input value={sourceName} onChange={event => setSourceName(event.target.value)} placeholder={method === 'agent' ? 'Example: Office Windows PC' : method === 'webhook' ? 'Example: Defender Alerts' : method === 'syslog' ? 'Example: Branch Firewall' : 'Example: Incident Evidence'} /></label>
        {method === 'agent' ? <>
          <div className="agent-platforms"><label><span>DEVICE OS</span><select defaultValue="windows"><option value="windows">Windows 10 / 11 / Server</option><option value="linux">Linux Server / Workstation</option></select></label><label><span>COLLECTION PROFILE</span><select defaultValue="security"><option value="security">Security Events</option><option value="system">Security + System</option><option value="full">Full Endpoint Telemetry</option></select></label></div>
          <div className="live-agent-banner"><i><span/></i><div><b>RUNS 24/7 IN THE BACKGROUND</b><p>Starts automatically with the device, queues logs during internet loss, and securely retries when the network returns.</p></div></div>
          <div className="direct-info-row agent-features"><span><small>TRANSPORT</small><b>ENCRYPTED HTTPS</b></span><span><small>HEARTBEAT</small><b>EVERY 60 SECONDS</b></span><span><small>OFFLINE QUEUE</small><b>AUTOMATIC RETRY</b></span></div>
          <div className="endpoint-preview"><span>COLLECTOR PACKAGE</span><code>Available after backend activation</code></div>
        </> : method === 'webhook' ? <>
          <div className="direct-info-row"><span><small>PAYLOAD FORMAT</small><b>JSON</b></span><span><small>AUTHENTICATION</small><b>HMAC SIGNATURE</b></span><span><small>DELIVERY</small><b>HTTPS POST</b></span></div>
          <div className="endpoint-preview"><span>INGESTION ENDPOINT</span><code>Generated after backend activation</code></div>
        </> : method === 'syslog' ? <>
          <div className="form-split"><label><span>TRANSPORT</span><select defaultValue="tls"><option value="tls">TCP + TLS</option><option value="tcp">TCP</option><option value="udp">UDP</option></select></label><label><span>LISTENER PORT</span><input value="6514" readOnly /></label></div>
          <div className="direct-guidance">A lightweight collector will securely forward remote device logs to AegisFlow.</div>
        </> : <>
          <label className="direct-drop"><input type="file" accept=".log,.json,.csv,.evtx" /><i>↑</i><b>Choose security log file</b><small>LOG, JSON, CSV and EVTX · processing starts after backend activation</small></label>
        </>}
        {directNotice ? <div className="siem-notice ok">✓<span>Direct source UI saved for review. Backend ingestion endpoint is the next implementation step.</span></div> : null}
        <div className="siem-actions"><button type="button" className="secondary-action" onClick={() => setDirectNotice(false)}>Reset</button><button type="button" className="primary-action" disabled={!sourceName.trim()} onClick={() => setDirectNotice(true)}>Save Source Setup</button></div>
      </div>
    </section>
    <aside className="connection-summary direct-summary">
      <div className="summary-signal"><span/><div><small>24/7 COLLECTOR SIGNAL</small><b>AGENT OFFLINE</b><p>No live device connected yet</p></div></div>
      <div className="direct-pipeline">
        <span><i>01</i><b>Collect Continuously</b><small>Background agent watches device logs</small></span>
        <span><i>02</i><b>Send Securely</b><small>Encrypted batches with offline retry</small></span>
        <span><i>03</i><b>Detect Threats</b><small>Rules filter suspicious activity</small></span>
        <span><i>04</i><b>AI Investigation</b><small>Create incidents and request approval</small></span>
      </div>
      <div className="direct-security-note"><b>RAW LOG SAFETY</b><p>Raw telemetry is parsed and filtered first. Only suspicious events continue to AI investigation.</p></div>
      <p className="credential-note">The dashboard does not need to stay open. Status turns ONLINE only after the real device collector sends its first heartbeat.</p>
    </aside>
  </div>
}

function ConnectionSignal({ connection }: { connection?: SiemConnection }) { return <div className={`connection-pill ${connection?.connected ? 'connected' : ''}`}><span/>{connection?.connected ? `${connection.provider.toUpperCase()} CONNECTED` : 'NOT CONNECTED'}</div> }
function formatTime(value?: string | null) { return value ? new Date(value).toLocaleString() : 'Never' }
