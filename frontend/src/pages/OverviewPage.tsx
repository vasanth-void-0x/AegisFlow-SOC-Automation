import { useEffect, useState, type CSSProperties } from 'react'
import type React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { DashboardKpis, Incident, TimelineEvent } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

export function OverviewPage() {
  const [incidents,setIncidents]=useState<Incident[]|null>(null)
  const [kpis,setKpis]=useState<DashboardKpis|null>(null)
  const [timeline,setTimeline]=useState<TimelineEvent[]>([])
  const [incidentsExpanded,setIncidentsExpanded]=useState(false)
  const [error,setError]=useState<string|null>(null)
  useEffect(()=>{Promise.all([api.listIncidents({page:1,page_size:50}),api.getDashboardKpis(),api.getAuditTimeline(12)]).then(([incidentsResult,kpiResult,timelineResult])=>{setIncidents(incidentsResult.items);setKpis(kpiResult);setTimeline(timelineResult)}).catch(e=>setError(e.message))},[])
  if(error)return <div className="page-pad"><ErrorState message={error}/></div>
  if(!incidents||!kpis)return <div className="page-pad"><LoadingState label="Synchronizing incident telemetry"/></div>
  const recent=incidents.slice(0,7),total=Math.max(kpis.total_alerts,1)
  return <div className="overview-page page-pad">
    <section className="page-intro"><div><span className="section-kicker">REAL-TIME VISIBILITY · INTELLIGENT AUTOMATION · RAPID RESPONSE</span><h1>SOC Command Center</h1><p>AegisFlow investigation and response automation platform.</p></div><SiemHeaderSignal kpis={kpis}/></section>

    <section className="command-layout command-layout-wide">
      <div className="command-main">
        <ArchitectureCore/>
        <section className="metric-grid lower-metrics compact-kpis">
          <Metric label="Active Incidents" value={kpis.active_incidents} accent="var(--color-signal)" note="Requires analyst attention" icon="incident"/>
          <Metric label="Critical Threats" value={kpis.critical_alerts} accent="var(--color-sev-critical)" note={Math.round(kpis.critical_alerts/total*100)+'% of total volume'} icon="critical"/>
          <Metric label="High Severity" value={kpis.high_alerts} accent="var(--color-sev-high)" note={Math.round(kpis.high_alerts/total*100)+'% of total volume'} icon="threat"/>
          <Metric label="Contained Threats" value={kpis.contained_threats} accent="var(--color-sev-medium)" note="Response action completed" icon="shield"/>
        </section>
        <section className="overview-compact-grid">
          <Panel title="Live Incident Stream" subtitle={recent.length+' latest security events'} action={<button className="panel-link expand-button" onClick={()=>setIncidentsExpanded(true)}>EXPAND ↗</button>} className="incident-panel compact-incident-panel">
            {recent.length===0?<div className="compact-empty"><strong>{kpis.connection_status==='connected'?'SIEM connected — no alerts received':'No SIEM connected'}</strong><Link to="/settings">CONNECT SIEM →</Link></div>:<div className="incident-list">{recent.slice(0,4).map(i=><IncidentRow key={i.id} incident={i}/>)}</div>}
          </Panel>
          <AutomationTimeline events={timeline}/>
        </section>
      </div>
    </section>
    <section className="capability-strip" aria-label="AegisFlow engineering coverage">
      <Capability value="11" label="AUTOMATION PHASES" detail="End-to-end SOC workflow"/><Capability value="07" label="MCP SECURITY TOOLS" detail="Typed and audit logged"/><Capability value="06" label="RAG RUNBOOKS" detail="Evidence-linked guidance"/><Capability value="110" label="TEST SCENARIOS" detail="Backend security coverage"/>
    </section>
    {incidentsExpanded?<IncidentOverlay incidents={incidents} onClose={()=>setIncidentsExpanded(false)}/>:null}
  </div>
}

function AutomationTimeline({events}:{events:TimelineEvent[]}){return <Panel title="Automation Timeline" subtitle="Latest investigation and response activity" action={<Link to="/audit" className="panel-link">VIEW AUDIT →</Link>}><div className="automation-timeline">{events.length===0?<div className="timeline-empty">Automation events will appear after a SIEM incident is processed.</div>:events.slice(0,6).map((event,index)=><div className="timeline-event" key={event.id}><i className={event.event_type.includes('approved')||event.event_type.includes('executed')?'success':event.event_type.includes('failed')?'danger':''}>{index+1}</i><div><b>{event.event_type.replaceAll('_',' ').toUpperCase()}</b><p>{event.description}</p><small>{new Date(event.created_at).toLocaleString()} · {event.actor}</small></div></div>)}</div></Panel>}

function IncidentOverlay({incidents,onClose}:{incidents:Incident[];onClose:()=>void}){useEffect(()=>{const close=(event:KeyboardEvent)=>event.key==='Escape'&&onClose();window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)},[onClose]);return <div className="incident-overlay" role="dialog" aria-modal="true" aria-label="All live incidents"><div className="incident-overlay-card"><header><div><span className="section-kicker">REAL SIEM TELEMETRY</span><h2>Live Incident Stream</h2></div><button onClick={onClose} aria-label="Close incident stream">×</button></header><div className="incident-overlay-list">{incidents.length?incidents.map(i=><IncidentRow key={i.id} incident={i}/>):<div className="compact-empty"><strong>No incidents received</strong><Link to="/settings" onClick={onClose}>CONNECT SIEM →</Link></div>}</div></div></div>}

function SiemHeaderSignal({kpis}:{kpis:DashboardKpis}){const online=kpis.connection_status==='connected';return <Link to="/settings" className={`siem-header-signal ${online?'online':''}`}><span/><div><b>{online?`${kpis.provider?.toUpperCase()} CONNECTED`:'SIEM OFFLINE'}</b><small>{online?(kpis.last_synced_at?`Synced ${new Date(kpis.last_synced_at).toLocaleTimeString()}`:'Ready for first sync'):'Connect a telemetry source'}</small></div><em>SETTINGS →</em></Link>}

function ArchitectureCore(){
  return <section className="architecture-core hero-spacer" aria-label="AegisFlow architecture: SIEM, IOC, RAG, MCP and SOAR connected to the SOC automation core"><div className="hero-live"><span/>LIVE ARCHITECTURE</div></section>
}
function MetricIcon({name}:{name:string}){const paths:Record<string,React.ReactNode>={incident:<><path d="M4 20V9l8-5 8 5v11"/><path d="M8 20v-6h8v6M12 7v3"/></>,critical:<><path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17h.01"/></>,threat:<><circle cx="12" cy="12" r="8"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M9 12h6"/></>,shield:<><path d="M12 3 4 6v6c0 5 3 8 8 10 5-2 8-5 8-10V6z"/><path d="m9 12 2 2 4-4"/></>};return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>}
function Metric({label,value,accent,note,icon}:{label:string;value:number;accent:string;note:string;icon:string}){return <div className="metric-card" style={{'--metric-accent':accent} as CSSProperties}><div className="metric-top"><span>{label}</span><i><MetricIcon name={icon}/></i></div><div className="metric-value"><strong>{String(value).padStart(2,'0')}</strong><svg viewBox="0 0 100 32" preserveAspectRatio="none"><path d="M1 27 15 23 27 25 41 14 54 18 68 8 82 12 99 3"/></svg></div><div className="metric-note"><span/> {note}</div></div>}
function Capability({value,label,detail}:{value:string;label:string;detail:string}){return <div className="capability"><strong>{value}</strong><div><b>{label}</b><span>{detail}</span></div><i>VERIFIED</i></div>}
function IncidentRow({incident}:{incident:Incident}){return <Link to={`/incidents/${incident.id}`} className="incident-row"><span className="severity-line" style={{background:severityColor(incident.severity)}}/><div className="incident-icon">!</div><div className="incident-main"><b>{incident.alert_name}</b><span>{incident.source} · {incident.id}</span></div><time>{new Date(incident.created_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</time><SeverityBadge severity={incident.severity}/><StatusBadge status={incident.status}/><span className="row-arrow">›</span></Link>}
