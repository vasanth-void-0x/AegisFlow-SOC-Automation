import { useEffect, useState, type CSSProperties } from 'react'
import type React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { DashboardKpis, Incident, ResponseProposal, TimelineEvent } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

export function OverviewPage() {
  const [incidents,setIncidents]=useState<Incident[]|null>(null)
  const [kpis,setKpis]=useState<DashboardKpis|null>(null)
  const [timeline,setTimeline]=useState<TimelineEvent[]>([])
  const [pendingApprovals,setPendingApprovals]=useState<ResponseProposal[]>([])
  const [incidentsExpanded,setIncidentsExpanded]=useState(false)
  const [error,setError]=useState<string|null>(null)
  useEffect(()=>{Promise.all([api.listIncidents({page:1,page_size:50}),api.getDashboardKpis(),api.getAuditTimeline(12)]).then(([incidentsResult,kpiResult,timelineResult])=>{setIncidents(incidentsResult.items);setKpis(kpiResult);setTimeline(timelineResult)}).catch(e=>setError(e.message))},[])
  useEffect(()=>{api.listApprovals({status:'pending'}).then(setPendingApprovals).catch(()=>setPendingApprovals([]))},[])
  if(error)return <div className="page-pad"><ErrorState message={error}/></div>
  if(!incidents||!kpis)return <div className="page-pad"><LoadingState label="Synchronizing incident telemetry"/></div>
  const recent=incidents.slice(0,7),total=Math.max(kpis.total_alerts,1)
  return <div className="overview-page page-pad">
    <section className="page-intro overview-intro"><div><span className="section-kicker">REAL-TIME VISIBILITY · INTELLIGENT AUTOMATION · RAPID RESPONSE</span><h1 className="overview-title">SOC AUTOMATION CENTER</h1><p>BlueOrch investigation and response automation platform.</p></div><SiemHeaderSignal kpis={kpis}/></section>

    <section className="command-layout command-layout-wide">
      <div className="command-main">
        <ArchitectureCore approvals={pendingApprovals}/>
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
    <section className="capability-strip" aria-label="BlueOrch engineering coverage">
      <Capability value="11" label="AUTOMATION PHASES" detail="End-to-end SOC workflow"/><Capability value="07" label="MCP SECURITY TOOLS" detail="Typed and audit logged"/><Capability value="06" label="RAG RUNBOOKS" detail="Evidence-linked guidance"/><Capability value="119" label="TEST SCENARIOS" detail="Backend security coverage"/>
    </section>
    <footer className="overview-footer">
      <span className="footer-copy">© 2026 <b>V</b></span>
      <nav className="footer-social" aria-label="Vasanth social links">
        <a href="https://github.com/vasanth-void-0x" target="_blank" rel="noreferrer" aria-label="GitHub"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.87c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.64-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 6.82a9.6 9.6 0 0 1 2.5.34c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86v2.76c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg><span>GitHub</span></a>
        <a href="https://www.linkedin.com/in/vasanth-2k4" target="_blank" rel="noreferrer" aria-label="LinkedIn"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 8.2H3.2V21h3.3V8.2ZM4.85 3A1.92 1.92 0 1 0 4.8 6.84 1.92 1.92 0 0 0 4.85 3ZM21 13.66c0-3.85-2.05-5.64-4.79-5.64a4.14 4.14 0 0 0-3.77 2.07V8.2H9.12V21h3.32v-6.34c0-1.67.32-3.29 2.39-3.29 2.04 0 2.07 1.91 2.07 3.4V21H21v-7.34Z"/></svg><span>LinkedIn</span></a>
        <a href="https://vasanth-portfolio-ten.vercel.app/" target="_blank" rel="noreferrer" aria-label="Portfolio"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none"/><path d="M3 12h18M12 3c2.4 2.5 3.7 5.5 3.7 9S14.4 18.5 12 21M12 3C9.6 5.5 8.3 8.5 8.3 12s1.3 6.5 3.7 9" fill="none"/></svg><span>Portfolio</span></a>
      </nav>
      <i className="footer-version">BLUEORCH v1.0.0</i>
    </footer>
    {incidentsExpanded?<IncidentOverlay incidents={incidents} onClose={()=>setIncidentsExpanded(false)}/>:null}
  </div>
}

function AutomationTimeline({events}:{events:TimelineEvent[]}){return <Panel title="Automation Timeline" subtitle="Latest investigation and response activity" action={<Link to="/audit" className="panel-link">VIEW AUDIT →</Link>}><div className="automation-timeline">{events.length===0?<div className="timeline-empty">Automation events will appear after a SIEM incident is processed.</div>:events.slice(0,6).map((event,index)=><div className="timeline-event" key={event.id}><i className={event.event_type.includes('approved')||event.event_type.includes('executed')?'success':event.event_type.includes('failed')?'danger':''}>{index+1}</i><div><b>{event.event_type.replaceAll('_',' ').toUpperCase()}</b><p>{event.description}</p><small>{new Date(event.created_at).toLocaleString()} · {event.actor}</small></div></div>)}</div></Panel>}

function IncidentOverlay({incidents,onClose}:{incidents:Incident[];onClose:()=>void}){useEffect(()=>{const close=(event:KeyboardEvent)=>event.key==='Escape'&&onClose();window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)},[onClose]);return <div className="incident-overlay" role="dialog" aria-modal="true" aria-label="All live incidents"><div className="incident-overlay-card"><header><div><span className="section-kicker">REAL SIEM TELEMETRY</span><h2>Live Incident Stream</h2></div><button onClick={onClose} aria-label="Close incident stream">×</button></header><div className="incident-overlay-list">{incidents.length?incidents.map(i=><IncidentRow key={i.id} incident={i}/>):<div className="compact-empty"><strong>No incidents received</strong><Link to="/settings" onClick={onClose}>CONNECT SIEM →</Link></div>}</div></div></div>}

function SiemHeaderSignal({kpis}:{kpis:DashboardKpis}){const online=kpis.connection_status==='connected';return <Link to="/settings" className={`siem-header-signal ${online?'online':''}`}><span/><div><b>{online?`${kpis.provider?.toUpperCase()} CONNECTED`:'SIEM OFFLINE'}</b><small>{online?(kpis.last_synced_at?`Synced ${new Date(kpis.last_synced_at).toLocaleTimeString()}`:'Ready for first sync'):'Connect a telemetry source'}</small></div><em>SETTINGS →</em></Link>}

function ArchitectureCore({approvals}:{approvals:ResponseProposal[]}){
  return <section className="architecture-core hero-spacer" aria-label="BlueOrch architecture: SIEM, IOC, RAG, MCP and SOAR connected to the SOC automation core"><div className="hero-live"><span/>LIVE ARCHITECTURE</div><HumanApprovalCard approvals={approvals}/></section>
}
function MetricIcon({name}:{name:string}){const paths:Record<string,React.ReactNode>={incident:<><path d="M4 20V9l8-5 8 5v11"/><path d="M8 20v-6h8v6M12 7v3"/></>,critical:<><path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17h.01"/></>,threat:<><circle cx="12" cy="12" r="8"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M9 12h6"/></>,shield:<><path d="M12 3 4 6v6c0 5 3 8 8 10 5-2 8-5 8-10V6z"/><path d="m9 12 2 2 4-4"/></>};return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>}
function Metric({label,value,accent,note,icon}:{label:string;value:number;accent:string;note:string;icon:string}){return <div className="metric-card" style={{'--metric-accent':accent} as CSSProperties}><div className="metric-top"><span>{label}</span><i><MetricIcon name={icon}/></i></div><div className="metric-value"><strong>{String(value).padStart(2,'0')}</strong><svg viewBox="0 0 100 32" preserveAspectRatio="none"><path d="M1 27 15 23 27 25 41 14 54 18 68 8 82 12 99 3"/></svg></div><div className="metric-note"><span/> {note}</div></div>}
function Capability({value,label,detail}:{value:string;label:string;detail:string}){return <div className="capability"><strong>{value}</strong><div><b>{label}</b><span>{detail}</span></div><i>VERIFIED</i></div>}
function HumanApprovalCard({approvals}:{approvals:ResponseProposal[]}){const proposal=approvals[0];return <section className={`overview-approval ${proposal?'pending':'clear'}`} aria-label="Human approval status"><div className="approval-card-top"><span>HUMAN APPROVAL</span><i>{proposal?'REVIEW':'CLEAR'}</i></div><div className="approval-card-value"><strong>{String(approvals.length).padStart(2,'0')}</strong><div><b>{proposal?'PENDING ACTIONS':'QUEUE CLEAR'}</b><small>{proposal?proposal.action_type.replaceAll('_',' ').toUpperCase():'No analyst decision required'}</small></div></div><Link to="/approvals">{proposal?'REVIEW & APPROVE':'OPEN CENTRE'} →</Link></section>}
function IncidentRow({incident}:{incident:Incident}){return <Link to={`/incidents/${incident.id}`} className="incident-row"><span className="severity-line" style={{background:severityColor(incident.severity)}}/><div className="incident-icon">!</div><div className="incident-main"><b>{incident.alert_name}</b><span>{incident.source} · {incident.id}</span></div><time>{new Date(incident.created_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</time><SeverityBadge severity={incident.severity}/><StatusBadge status={incident.status}/><span className="row-arrow">›</span></Link>}
