const SHIPPED = [
  ['MCP Security Gateway', 'Allowlisted tools, scoped API keys and immutable audit history.'],
  ['Deep AI Investigation', 'Evidence-led triage with MITRE mapping, runbooks and response proposals.'],
  ['Human-Gated Response', 'High-risk actions wait for analyst approval before execution.'],
  ['Live Agent Ingestion', 'Authenticated Windows telemetry, heartbeat tracking and resilient batching.'],
]
const UPCOMING = [
  ['01', 'Realtime event channel', 'Server-sent incident, approval, MCP and audit updates without polling delay.'],
  ['02', 'Wazuh response connector', 'Human-approved active response for endpoint and firewall actions.'],
  ['03', 'Operational observability', 'Centralized errors, workflow alerts, latency and AI usage metrics.'],
  ['04', 'Agent lifecycle controls', 'Key rotation, revocation, signed releases and resilient upgrades.'],
  ['05', 'Workflow resilience', 'Idempotent execution, bounded retries and dead-letter recovery.'],
  ['06', 'Production validation', 'Load, recovery, backup and deployment runbook verification.'],
]

export function AboutPage() {
  return <div className="about-page page-pad">
    <header className="about-hero"><span className="section-kicker">BLUEORCH PLATFORM</span><h1>Autonomous investigation.<br/><em>Human-controlled response.</em></h1><p>BlueOrch connects security telemetry, MCP tools, deep AI analysis and auditable approval workflows in one SOC automation command centre.</p></header>
    <section className="about-section"><div className="about-heading"><span>01</span><div><h2>MVP — operational today</h2><p>Complete single-team SOC automation flow, deployed and verified end to end.</p></div></div><div className="about-grid">{SHIPPED.map(([title,detail])=><article key={title}><i>✓</i><h3>{title}</h3><p>{detail}</p><small>ACTIVE</small></article>)}</div></section>
    <section className="about-section"><div className="about-heading"><span>02</span><div><h2>Next phase — production-ready pilot</h2><p>The MVP is complete. Upcoming work focuses on reliability, real response integrations and operational scale before any enterprise expansion.</p></div></div><div className="roadmap-grid">{UPCOMING.map(([number,title,detail])=><article key={number}><b>{number}</b><div><h3>{title}</h3><p>{detail}</p></div><span>UPCOMING</span></article>)}</div></section>
    <section className="about-principles"><div><b>SECURITY FIRST</b><span>Scoped credentials · signed sessions · append-only audit</span></div><div><b>HUMAN IN CONTROL</b><span>No high-risk response without analyst approval</span></div><div><b>EVIDENCE DRIVEN</b><span>Every recommendation traces back to observable data</span></div></section>
  </div>
}
