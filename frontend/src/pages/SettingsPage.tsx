import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import type { SiemConnectInput, SiemConnection, SiemProvider } from '../api/types'
import { LoadingState } from '../components/Panel'

const INITIAL: SiemConnectInput = {
  provider: 'splunk', base_url: '', token: '', username: '', password: '', index_name: '', verify_ssl: true,
}

export function SettingsPage() {
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
    <section className="page-intro"><div><span className="section-kicker">REAL TELEMETRY · ENCRYPTED CREDENTIALS · NO DEMO DATA</span><h1>SIEM Connections</h1><p>Connect AegisFlow directly to your security data source.</p></div></section>
    <div className="siem-layout">
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
    </div>
  </div>
}

function ConnectionSignal({ connection }: { connection?: SiemConnection }) { return <div className={`connection-pill ${connection?.connected ? 'connected' : ''}`}><span/>{connection?.connected ? `${connection.provider.toUpperCase()} CONNECTED` : 'NOT CONNECTED'}</div> }
function formatTime(value?: string | null) { return value ? new Date(value).toLocaleString() : 'Never' }
