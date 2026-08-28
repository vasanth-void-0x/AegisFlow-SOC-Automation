import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import type { SiemConnectInput, SiemConnection, SiemProvider } from '../api/types'
import { LoadingState } from '../components/Panel'

const INITIAL: SiemConnectInput = {
  provider: 'splunk', base_url: '', token: '', username: '', password: '', index_name: '', verify_ssl: true,
}

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
      <button type="button" className={sourceMode === 'siem' ? 'active' : ''} onClick={() => { setSourceMode('siem'); setNotice(null) }}><i>01</i><span><b>SIEM Integration</b><small>Splunk · Wazuh</small></span><em>{connections.some(item => item.connected) ? 'ONLINE' : 'OFFLINE'}</em></button>
      <button type="button" className={sourceMode === 'direct' ? 'active' : ''} onClick={() => { setSourceMode('direct'); setNotice(null) }}><i>02</i><span><b>Direct Log Source</b><small>24/7 Agent · Webhook · Syslog · File</small></span><em>SETUP</em></button>
    </nav>
    {sourceMode === 'siem' ? <div className="siem-layout">
      <section className="siem-card">
        <div className="siem-card-head"><div><span className="section-kicker">DATA SOURCE</span><h2>Configure SIEM</h2></div><ConnectionSignal connection={connected} /></div>
        <div className="provider-tabs" role="tablist" aria-label="SIEM provider">
          {(['splunk','wazuh'] as SiemProvider[]).map(item => <button type="button" role="tab" aria-selected={provider === item} className={provider === item ? 'active' : ''} key={item} onClick={() => { setForm({ ...INITIAL, provider: item, index_name: item === 'splunk' ? 'security' : 'wazuh-alerts-*' }); setNotice(null) }}><span className={`provider-logo ${item}`}>{item === 'splunk' ? 'S>' : 'W'}</span><b>{item === 'splunk' ? 'Splunk' : 'Wazuh'}</b><small>{item === 'splunk' ? 'Management API · 8089' : 'Indexer API · 9200'}</small></button>)}
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
