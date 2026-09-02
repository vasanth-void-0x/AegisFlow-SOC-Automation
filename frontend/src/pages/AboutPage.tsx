const SHIPPED = [
  ['MCP Security Gateway', 'Allowlisted tools, scoped API keys and immutable audit history.'],
  ['Deep AI Investigation', 'Evidence-led triage with MITRE mapping, runbooks and response proposals.'],
  ['Human-Gated Response', 'High-risk actions wait for analyst approval before execution.'],
  ['Live Agent Ingestion', 'Authenticated Windows telemetry, heartbeat tracking and resilient batching.'],
]
const UPCOMING = [
  ['01', 'VirusTotal enrichment hardening', 'Provider health, quota visibility and fallback evidence.'],
  ['02', 'Multi-tenant SOC workspaces', 'Tenant isolation, scoped agents and organization policies.'],
  ['03', 'Linux collector package', 'Native systemd service, journald collection and signed updates.'],
  ['04', 'Advanced response connectors', 'Production EDR, firewall, IAM and ticketing integrations.'],
  ['05', 'Investigation analytics', 'MTTD/MTTR trends, model quality and analyst decision metrics.'],
  ['06', 'Realtime event channel', 'Server-pushed incident and approval updates without polling delay.'],
]

export function AboutPage() {
  return <div className="about-page page-pad">
    <header className="about-hero"><span className="section-kicker">BLUEORCH PLATFORM</span><h1>Autonomous investigation.<br/><em>Human-controlled response.</em></h1><p>BlueOrch connects security telemetry, MCP tools, deep AI analysis and auditable approval workflows in one SOC automation command centre.</p></header>
    <section className="about-section"><div className="about-heading"><span>01</span><div><h2>Operational today</h2><p>Production capabilities already implemented and verified.</p></div></div><div className="about-grid">{SHIPPED.map(([title,detail])=><article key={title}><i>✓</i><h3>{title}</h3><p>{detail}</p><small>ACTIVE</small></article>)}</div></section>
    <section className="about-section"><div className="about-heading"><span>02</span><div><h2>Upcoming implementations</h2><p>Planned engineering roadmap after the current production baseline.</p></div></div><div className="roadmap-grid">{UPCOMING.map(([number,title,detail])=><article key={number}><b>{number}</b><div><h3>{title}</h3><p>{detail}</p></div><span>PLANNED</span></article>)}</div></section>
    <section className="about-principles"><div><b>SECURITY FIRST</b><span>Scoped credentials · signed sessions · append-only audit</span></div><div><b>HUMAN IN CONTROL</b><span>No high-risk response without analyst approval</span></div><div><b>EVIDENCE DRIVEN</b><span>Every recommendation traces back to observable data</span></div></section>
  </div>
}
