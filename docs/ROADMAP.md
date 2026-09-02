# BlueOrch Delivery Roadmap

BlueOrch uses capability-based stages. A feature belongs to a stage only after its behavior is implemented,
tested, documented, and demonstrated without overstating simulated or provider-dependent results.

## Stage 1 — MVP complete

**Goal:** prove the complete single-team SOC automation loop safely.

- Multiple telemetry inputs with normalization and deduplication.
- Windows collector heartbeat, batching and disk retry.
- VirusTotal/GeoIP/MITRE enrichment with explicit provider states.
- Groq structured investigation with labelled fallback.
- RAG-backed SOC runbooks with citations.
- Seven authenticated, allowlisted, audited MCP tools.
- n8n V3.1 orchestration and retry branch.
- Human approval before safe simulated response.
- Admin/Analyst/Viewer RBAC and signed sessions.
- Live React incident, approval, MCP, audit, agent and health views.
- End-to-end verification, 131 backend tests and production frontend build.

## Stage 2 — Production-ready pilot (next)

**Goal:** run a controlled pilot with reliable operations and one real response integration.

| Workstream | Exit criterion |
|---|---|
| Realtime delivery | SSE or equivalent pushes incident, approval, MCP and audit changes without page polling |
| Wazuh integration | Human-approved active response works in a controlled lab with dry-run default |
| Observability | Structured errors, latency, workflow failures, agent health and AI usage are visible |
| Agent lifecycle | Device keys can be rotated/revoked and releases are signed |
| Workflow resilience | Claims are idempotent; retries are bounded; failed work has a recovery path |
| Data reliability | Backups, restore procedure, retention and migration path are exercised |
| Operational validation | Load, failure recovery and deployment runbooks pass a recorded test |

## Stage 3 — Enterprise platform (future)

This stage is intentionally not part of the MVP or production-pilot claim:

- Multi-tenant organization isolation.
- SSO/SAML/OIDC, MFA and centralized identity lifecycle.
- Custom policy and fine-grained organization roles.
- High availability, horizontal scaling and regional strategy.
- Compliance reporting, retention policy controls and SLA operations.
- Multiple production EDR, firewall, IAM and case-management connectors.
- Signed automatic agent upgrades and fleet management.

## Scope rule

The README and UI must keep these labels distinct:

> **Current:** MVP complete  
> **Next:** Production-ready pilot  
> **Future:** Enterprise SOC platform
