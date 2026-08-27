import { useEffect, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Incident } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

export function OverviewPage() {
  const [incidents,setIncidents]=useState<Incident[]|null>(null)
  const [error,setError]=useState<string|null>(null)
  useEffect(()=>{api.listIncidents({page:1,page_size:50}).then(r=>setIncidents(r.items)).catch(e=>setError(e.message))},[])
  if(error)return <div className="page-pad"><ErrorState message={error}/></div>
  if(!incidents)return <div className="page-pad"><LoadingState label="Synchronizing incident telemetry"/></div>
  const counts={critical:0,high:0,medium:0,low:0};const open=new Set(['new','triaging','pending_approval']);let openCount=0
  incidents.forEach(i=>{counts[i.severity]++;if(open.has(i.status))openCount++})
  const recent=incidents.slice(0,7),total=Math.max(incidents.length,1)
  return <div className="overview-page page-pad">
    <section className="page-intro"><div><span className="section-kicker">REAL-TIME SECURITY POSTURE</span><h1>SOC Command Overview</h1><p>Live incident telemetry, triage state and response readiness from the AegisFlow pipeline.</p></div><div className="sync-badge"><span/>Pipeline synchronized</div></section>
    <section className="metric-grid">
      <Metric label="Open Incidents" value={openCount} accent="var(--color-signal)" note="Requires analyst attention" glyph="01"/>
      <Metric label="Critical Threats" value={counts.critical} accent="var(--color-sev-critical)" note={Math.round(counts.critical/total*100)+'% of total volume'} glyph="C"/>
      <Metric label="High Severity" value={counts.high} accent="var(--color-sev-high)" note={Math.round(counts.high/total*100)+'% of total volume'} glyph="H"/>
      <Metric label="Medium / Low" value={counts.medium+counts.low} accent="var(--color-sev-medium)" note="Monitored by automation" glyph="M"/>
    </section>
    <section className="overview-grid">
      <Panel title="Live Incident Stream" subtitle={recent.length+' latest security events'} action={<Link to="/incidents" className="panel-link">OPEN QUEUE →</Link>} className="incident-panel">
        {recent.length===0?<div className="empty-radar"><div className="radar-ring"/><b>No incidents detected</b><span>The pipeline is monitoring incoming sources.</span></div>:<div className="incident-list">{recent.map(i=><IncidentRow key={i.id} incident={i}/>)}</div>}
      </Panel>
      <div className="right-stack">
        <Panel title="Threat Distribution" subtitle="Current severity mix">
          <div className="distribution-ring" style={{background:`conic-gradient(${severityColor('critical')} 0 ${counts.critical/total*100}%,${severityColor('high')} 0 ${(counts.critical+counts.high)/total*100}%,${severityColor('medium')} 0 ${(counts.critical+counts.high+counts.medium)/total*100}%,${severityColor('low')} 0 100%)`}}><div><b>{incidents.length}</b><span>TOTAL</span></div></div>
          <div className="legend">{(['critical','high','medium','low'] as const).map(s=><div key={s}><span style={{background:severityColor(s)}}/><label>{s}</label><b>{counts[s]}</b></div>)}</div>
        </Panel>
        <Panel title="Automation Pipeline" subtitle="Response workflow status"><div className="pipeline-steps">{['Ingest','Enrich','AI Triage','Approve','Respond'].map((s,n)=><div key={s}><span>{String(n+1).padStart(2,'0')}</span><div><b>{s}</b><small>{n===4?'SIMULATED':'OPERATIONAL'}</small></div></div>)}</div></Panel>
      </div>
    </section>
  </div>
}
function Metric({label,value,accent,note,glyph}:{label:string;value:number;accent:string;note:string;glyph:string}){return <div className="metric-card" style={{'--metric-accent':accent} as CSSProperties}><div className="metric-top"><span>{label}</span><i>{glyph}</i></div><strong>{String(value).padStart(2,'0')}</strong><div className="metric-note"><span/> {note}</div></div>}
function IncidentRow({incident}:{incident:Incident}){return <Link to={`/incidents/${incident.id}`} className="incident-row"><span className="severity-line" style={{background:severityColor(incident.severity)}}/><div className="incident-icon">!</div><div className="incident-main"><b>{incident.alert_name}</b><span>{incident.source} · {incident.id}</span></div><time>{new Date(incident.created_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</time><SeverityBadge severity={incident.severity}/><StatusBadge status={incident.status}/><span className="row-arrow">›</span></Link>}
