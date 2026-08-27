import { useEffect, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Incident } from '../api/types'
import { Panel, LoadingState, ErrorState } from '../components/Panel'
import { SeverityBadge, severityColor } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'

const PIPELINE = [
  ['01','Ingest','Collect telemetry & alerts','LIVE'],
  ['02','Enrich','Add IOC context & threat intel','LIVE'],
  ['03','AI Triage','Prioritize with AI/ML','ACTIVE'],
  ['04','Investigate','Automated evidence analysis','READY'],
  ['05','Approve','Human-in-the-loop decision','GATED'],
  ['06','Respond','Simulated containment','SAFE'],
]

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
    <section className="page-intro"><div><span className="section-kicker">REAL-TIME VISIBILITY · INTELLIGENT AUTOMATION · RAPID RESPONSE</span><h1>SOC Command Center</h1><p>AegisFlow investigation and response automation platform.</p></div><div className="sync-badge"><span/>Automation active</div></section>

    <section className="command-layout">
      <div className="command-main">
        <ArchitectureCore/>
        <Panel title="Live Incident Stream" subtitle={recent.length+' latest security events'} action={<Link to="/incidents" className="panel-link">VIEW ALL →</Link>} className="incident-panel">
          {recent.length===0?<div className="empty-radar"><div className="radar-visual"><span/><i/><b/></div><strong>Monitoring all configured sources</strong><p>No active incidents. AegisFlow is ready to ingest SIEM, EDR or webhook alerts.</p><Link to="/health">VIEW SYSTEM READINESS →</Link></div>:<div className="incident-list">{recent.map(i=><IncidentRow key={i.id} incident={i}/>)}</div>}
        </Panel>
      </div>
      <aside className="response-rail">
        <Panel title="AegisFlow Response Pipeline" subtitle="Investigation workflow">
          <div className="response-pipeline">{PIPELINE.map(([n,name,detail,status],idx)=><div className="response-step" key={n}><div className="step-node">{n}</div>{idx<PIPELINE.length-1&&<span className="step-line"/>}<div className="step-copy"><b>{name}</b><small>{detail}</small></div><i className={status==='GATED'?'gated':''}>{status}</i></div>)}</div>
          <div className="readiness"><div><span>PIPELINE READINESS</span><b>92%</b></div><div className="readiness-bar"><i/><i/><i/><i/><i/><i/><i/><i/><i/><span/></div></div>
        </Panel>
        <Panel title="System Status" subtitle="Core service readiness">
          <div className="system-list">{['SIEM Connectivity','MCP Orchestrator','SOAR Platform','RAG Service','Threat Intel Feeds','Automation Engine'].map(x=><div key={x}><span>{x}</span><b>HEALTHY</b><i/></div>)}</div>
        </Panel>
      </aside>
    </section>

    <section className="metric-grid lower-metrics">
      <Metric label="Open Incidents" value={openCount} accent="var(--color-signal)" note="Requires analyst attention" glyph="01"/>
      <Metric label="Critical Threats" value={counts.critical} accent="var(--color-sev-critical)" note={Math.round(counts.critical/total*100)+'% of total volume'} glyph="C"/>
      <Metric label="High Severity" value={counts.high} accent="var(--color-sev-high)" note={Math.round(counts.high/total*100)+'% of total volume'} glyph="H"/>
      <Metric label="Medium / Low" value={counts.medium+counts.low} accent="var(--color-sev-medium)" note="Monitored by automation" glyph="M"/>
    </section>
    <section className="capability-strip" aria-label="AegisFlow engineering coverage">
      <Capability value="11" label="AUTOMATION PHASES" detail="End-to-end SOC workflow"/><Capability value="07" label="MCP SECURITY TOOLS" detail="Typed and audit logged"/><Capability value="06" label="RAG RUNBOOKS" detail="Evidence-linked guidance"/><Capability value="110" label="TEST SCENARIOS" detail="Backend security coverage"/>
    </section>
  </div>
}

function ArchitectureCore(){
  const nodes=[['siem','SIEM','Telemetry Ingestion'],['ioc','IOC','Threat Intelligence'],['rag','RAG','Knowledge & Runbooks'],['mcp','MCP','Automation Protocol'],['soar','SOAR','Response Automation']]
  return <section className="architecture-core"><div className="circuit-lines"/>{nodes.map(([pos,name,detail])=><div key={name} className={`arch-node ${pos}`}><i/ ><div><b>{name}</b><span>{detail}</span><small>Live <em/></small></div></div>)}<div className="processor-chip"><span>AEGISFLOW</span><small>SOC AUTOMATION CORE</small><i/><i/><i/><i/></div></section>
}
function Metric({label,value,accent,note,glyph}:{label:string;value:number;accent:string;note:string;glyph:string}){return <div className="metric-card" style={{'--metric-accent':accent} as CSSProperties}><div className="metric-top"><span>{label}</span><i>{glyph}</i></div><strong>{String(value).padStart(2,'0')}</strong><div className="metric-note"><span/> {note}</div></div>}
function Capability({value,label,detail}:{value:string;label:string;detail:string}){return <div className="capability"><strong>{value}</strong><div><b>{label}</b><span>{detail}</span></div><i>VERIFIED</i></div>}
function IncidentRow({incident}:{incident:Incident}){return <Link to={`/incidents/${incident.id}`} className="incident-row"><span className="severity-line" style={{background:severityColor(incident.severity)}}/><div className="incident-icon">!</div><div className="incident-main"><b>{incident.alert_name}</b><span>{incident.source} · {incident.id}</span></div><time>{new Date(incident.created_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</time><SeverityBadge severity={incident.severity}/><StatusBadge status={incident.status}/><span className="row-arrow">›</span></Link>}
