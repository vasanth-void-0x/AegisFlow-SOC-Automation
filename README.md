# BlueOrch — SOC Investigation & Response Automation Platform

[![Live](https://img.shields.io/badge/LIVE-SOC%20DASHBOARD-28d7f2?style=for-the-badge&logo=vercel&logoColor=white)](https://blueorch-soc-automation.vercel.app/)
[![React](https://img.shields.io/badge/React-TypeScript-087ea4?style=flat-square&logo=react)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)](backend/)
[![Tests](https://img.shields.io/badge/Backend%20Tests-127%20Passing-3ecf8e?style=flat-square)](#testing)

### [Launch the live SOC dashboard →](https://blueorch-soc-automation.vercel.app/)

![BlueOrch SOC Command Center](docs/screenshots/blueorch-live-command-overview.jpg)

BlueOrch is a working, end-to-end SOC (Security Operations Center) automation platform. It ingests
alerts from Splunk/Wazuh or receives endpoint logs directly through an agent, webhook, syslog relay, or
file pipeline. It normalizes events, enriches indicators of compromise, runs structured LLM-based triage, retrieves relevant
SOC runbooks with RAG, exposes seven allowlisted security tools through an authenticated remote MCP gateway, orchestrates deep investigation with n8n V3,
requires human approval before any response action executes, and produces an evidence-linked final report.

**This is a real system, not a demo with static values.** Every screen in the dashboard is backed by a
live API call. Where a paid provider (Groq, VirusTotal) isn't configured, the system falls back to
clearly-labeled demo/fallback behavior instead of pretending to have data it doesn't.

The desktop-first command center uses fixed navigation and response rails, a live processor topology,
animated circuit telemetry, health monitoring, incident investigation views, approval controls, and
evidence-linked SOC automation workflows.

## Project status

| Phase | Description | Status |
|---|---|---|
| 1 | Alert ingestion & storage | ✅ |
| 2 | Threat-intel enrichment (VirusTotal, GeoIP, MITRE) | ✅ |
| 3 | Structured AI triage (Groq) | ✅ |
| 4 | RAG-based SOC runbooks | ✅ |
| 5 | MCP security server (7 tools) | ✅ |
| 6 | n8n orchestration workflow | ✅ |
| 7 | Human approval & response | ✅ |
| 8 | React SOC dashboard | ✅ |
| 9 | Security tests | ✅ |
| 10 | AI evaluation | ✅ |
| 11 | Docker & CI | ✅ (Docker builds are syntax-validated, not build-tested — see [Limitations](#known-limitations--honest-notes)) |
| 12 | Splunk & Wazuh SIEM connectivity | ✅ |
| 13 | Direct log normalization, deduplication & bulk ingestion | ✅ |
| 14 | Windows 24×7 Event Log collector, heartbeat & disk retry | ✅ |
| 15 | Final incident report API | ✅ |
| 16 | Authenticated remote MCP HTTPS gateway & shared audit executor | ✅ |
| 17 | Evidence-grounded deep AI investigation | ✅ |
| 18 | n8n MCP Deep Investigation V3 | ✅ |
| 19 | End-to-end agent → MCP → approval → contained verification | ✅ |

**127 backend tests passing** in the verified combined FastAPI/MCP test suite.

## Architecture

```mermaid
flowchart TB
    subgraph Ingestion
        A[Splunk / Wazuh] -->|SIEM sync| B[FastAPI Backend]
        O[Endpoint / Server Logs] --> P[BlueOrch Collector]
        P -->|Authenticated heartbeat + bulk events| B
        Q[Webhook / Syslog Relay / File] -->|single or bulk logs| B
    end

    subgraph Backend["Backend (FastAPI + SQLAlchemy + SQLite)"]
        B --> C[Incident Store]
        C --> D[Threat-Intel Enrichment<br/>VirusTotal + GeoIP + MITRE]
        D --> E[Deep AI Investigation<br/>Groq structured JSON]
        F[RAG Retriever<br/>SOC Runbooks] --> E
        E --> G[Evidence-based Proposal<br/>pending approval]
        G --> H[Human Approval API]
        H --> I[Simulated Response<br/>block_ip / isolate_host]
        C --> J[Immutable Timeline]
        J --> R[Final Incident Report]
    end

    subgraph MCP["Authenticated Remote MCP Gateway"]
        K[7 typed + allowlisted tools] --> C
        K --> D
        K --> F
        K --> G
        K --> S[Audited Tool History]
    end

    subgraph Orchestration
        L[n8n MCP V3] -->|poll + claim| B
        L -->|X-BlueOrch-MCP-Key| K
        L --> E
        L --> G
    end

    M[React Dashboard] -->|REST| B
    N[MCP Client<br/>e.g. Claude Desktop] --> K
```

## Repository structure

```text
BlueOrch-SOC-Automation/
├── backend/               FastAPI app, MCP server, tests
│   ├── app/
│   │   ├── api/            Route handlers
│   │   ├── core/            Config, logging, rate limiting
│   │   ├── database/        SQLAlchemy session/engine
│   │   ├── models/           ORM models (incidents, triage, proposals, timeline, mcp audit)
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── services/          Business logic
│   │   ├── integrations/      External API clients (VirusTotal)
│   │   ├── ai/                 Groq client + triage orchestration
│   │   ├── rag/                 Chunking, embeddings, vector store, retriever
│   │   └── mcp_server/           MCP tools, schemas, audit, redaction
│   ├── tests/                    127 tests
│   ├── requirements.txt           Main backend deps
│   └── requirements-mcp.txt        Isolated MCP server deps (see below)
├── frontend/                React + TypeScript + Vite SOC dashboard
├── n8n/                      Importable workflow JSON + error handler
├── collector/                 Windows Event Log agent + scheduled-task installer
├── runbooks/                  6 SOC runbooks (Markdown, RAG-indexed)
├── evaluation/                  AI eval dataset + runner + report
├── sample-data/                   Safe fictional sample alerts
├── docs/                           Supplementary docs (MCP setup, n8n import)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Quick start (local, no Docker)

### 1. Backend

```bash
cd backend
python3 -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp ../.env.example .env   # demo mode works with zero keys

uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/v1/health` — you should see `{"status": "ok", ...}`.
Interactive API docs: `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/api/*` to the backend on port 8000.

### 3. MCP server (optional — needed only if an MCP client will connect)

The `mcp` SDK requires a newer `starlette` than FastAPI supports, so it lives in its own venv:

```bash
cd backend
python3 -m venv .venv-mcp
# activate as above, then:
pip install -r requirements-mcp.txt
python -m app.mcp_server.server
```

See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for connecting an MCP client.

### 4. n8n (optional — needed for the orchestration workflow)

```bash
docker run -it --rm -p 5678:5678 n8nio/n8n
```

For the MCP deep-investigation flow, set `BLUEORCH_MCP_KEY` in the n8n process
environment and import `n8n/blueorch-incident-automation-v3.json`.
Set `BLUEORCH_API_BASE=http://host.docker.internal:8000` when n8n runs in Docker, or
`http://backend:8000` with Docker Compose. See [n8n/README.md](n8n/README.md).

### 5. Test direct-log ingestion

```bash
curl -X POST http://localhost:8000/api/v1/logs/ingest \
  -H "Content-Type: application/json" \
  -H "X-BlueOrch-Key: $DIRECT_LOG_API_KEY" \
  -d '{"message":"Failed login brute force from 203.0.113.10 to 10.0.0.5","source_type":"agent","source_name":"windows-lab","event_id":"test-001"}'
```

For a deployed setup, first configure `DIRECT_LOG_REGISTRATION_TOKEN` and a persistent
`DATABASE_URL` in Vercel. In **Settings → Direct Log Source**, enter that registration token,
register `BLUEORCH-WIN-01`, and copy the one-time device API key.

Download/clone this repository on the Windows device. Open `collector` in **Administrator
PowerShell**, then install the 24×7 collector:

```powershell
.\install_windows.ps1 `
  -ApiUrl "https://blueorch-soc-automation.vercel.app" `
  -ApiKey "boa_COPY_THE_ONE_TIME_KEY" `
  -SourceName "BLUEORCH-WIN-01" `
  -Profile "security"
```

The installer creates a SYSTEM scheduled task that starts at boot. The agent reads new Windows
Security events (optionally System/Application), batches them over HTTPS, sends heartbeats, uses
stable record IDs for deduplication, and stores unsent events under `C:\ProgramData\BlueOrch\Agent`.
Use `Get-ScheduledTask -TaskName "BlueOrch Log Agent"` to verify it.

## Environment variables

See [.env.example](.env.example) for the full reference. Everything defaults to safe demo values —
Core local operation works without provider keys; live enrichment, remote MCP,
and deep AI require their corresponding secrets.

| Variable | Purpose | Required? |
|---|---|---|
| `GROQ_API_KEY` | Live AI triage | No — falls back to rule-based triage |
| `VIRUSTOTAL_API_KEY` | Live IOC reputation | Deep live investigation |
| `MCP_GATEWAY_API_KEY` | Authenticates remote n8n MCP tool calls | n8n V3 |
| `ENABLE_REAL_RESPONSE_ADAPTER` | Enable real (non-simulated) response actions | No — **must stay `false` unless you've implemented and reviewed a real adapter** |
| `DATABASE_URL` | Persistent Postgres URL (required for deployed 24×7 telemetry) | Production direct logs |
| `DIRECT_LOG_API_KEY` | Protects agent/webhook/bulk log-ingestion endpoints | Recommended for remote collectors |
| `DIRECT_LOG_REGISTRATION_TOKEN` | Admin secret used only to register/list collector devices | Agent setup |
| `BLUEORCH_API_BASE` | Backend base URL used by imported n8n workflows | Required in n8n |
| `SIEM_ENCRYPTION_KEY` | Encrypts stored Splunk/Wazuh credentials | Required when connecting SIEM |

## Testing

```bash
cd backend
python -m pytest -q   # 127 tests
```

Frontend:

```bash
cd frontend
npx tsc --noEmit    # type check
npm run build        # production build
```

AI evaluation:

```bash
cd backend
python ../evaluation/run_eval.py
```

See [evaluation/eval_report.md](evaluation/eval_report.md) for the latest run.

## Threat model (summary)

**In scope / mitigated:**
- SQL injection — parameterized queries via SQLAlchemy ORM throughout; tested in `test_security.py`.
- Prompt injection — the LLM's raw text output is never trusted; every triage response is validated
  against a strict Pydantic schema, and injected instructions in alert fields can at most influence the
  *content* of a still-schema-valid response, never bypass approval requirements (tested explicitly).
- Secret leakage — MCP audit logs and error messages are redacted (`app/mcp_server/redaction.py`);
  tested that API keys never appear in health checks or validation error bodies.
- Unauthorized response actions — every response proposal requires human approval; approved
  proposals cannot be re-approved; rejected/expired proposals cannot execute.
- Remote MCP abuse — gateway calls require `X-BlueOrch-MCP-Key`, tools are allowlisted and typed,
  execution is time-limited, sensitive fields are redacted, and success/failure is written to MCP Tool History.
- Oversized payloads / malformed JSON — request size limits and structured 422/413 handling.
- Rate limiting — per-IP sliding window middleware (configurable, default 120 req/min).
- Remote direct-log collection — optional `X-BlueOrch-Key` verification, payload limits,
  normalization, and event-id/fingerprint deduplication.

**Explicitly out of scope for this portfolio build:**
- The environment-backed Admin/Analyst/Viewer login is suitable for this portfolio deployment; a
  multi-user production SOC should replace it with an enterprise identity provider and managed sessions.
- Multi-tenant isolation.
- Encryption at rest for the SQLite database.
- The `ENABLE_REAL_RESPONSE_ADAPTER` flag exists but no real adapter is implemented — response actions
  are always simulated in this repository, by design.

## Known limitations & honest notes

- **Provider-dependent enrichment:** the deployed Groq deep-investigation and remote MCP paths have been
  exercised end to end. VirusTotal reports an explicit live, not-configured, rate-limited, or provider-error
  state; a valid key is required for live reputation results and no fallback is presented as VirusTotal data.
- **Docker images are syntax-validated, not build-tested** — Docker itself isn't available in the sandbox
  this was built in. The Dockerfiles and `docker-compose.yml` follow standard, well-tested patterns, but
  run `docker compose up --build` locally before relying on them in production.
- **RAG embeddings**: the primary path is `sentence-transformers` (downloads model weights from Hugging
  Face on first use). If that's unavailable, the system automatically falls back to a deterministic
  offline hashing-based vectorizer — lower semantic quality, but keeps RAG functional with zero external
  dependencies. Both paths are tested; `evaluation/eval_report.md` reports which one ran.
- **AI evaluation numbers reflect the rule-based fallback path** in this repository's committed report,
  since no Groq key was available at build time. Re-run `evaluation/run_eval.py` with `GROQ_API_KEY` set
  to get live-LLM metrics — see the report's own disclaimer for details.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ModuleNotFoundError: mcp.server.fastmcp` | You're using the main `.venv`, not `.venv-mcp`. The MCP server needs its own environment — see [docs/MCP_SETUP.md](docs/MCP_SETUP.md). |
| Frontend shows "Backend unreachable" | Backend isn't running on port 8000, or `vite.config.ts`'s proxy target doesn't match. Confirm `curl http://localhost:8000/health` works first. |
| `sentence-transformers unavailable ... using offline hashing embedding fallback` in logs | Expected if the Hugging Face model hasn't been downloaded yet (needs network) or the package isn't installed. RAG still works via the fallback — see [Known Limitations](#known-limitations--honest-notes). |
| `pip-audit` / `npm audit` failing CI | These run with `|| true` in CI so they report but don't block merges by default — tighten this once you've triaged existing findings. |
| n8n workflow can't reach the backend | If running n8n via Docker Compose, use `http://backend:8000` (the service name), not `localhost`, as `BLUEORCH_API_BASE`. |
| `409 Conflict` on alert ingestion | Expected — this is the dedup/idempotency protection working. Check the `X-Existing-Incident-Id` response header for the existing incident. |
| `401 Invalid collector API key` | Send the same value configured as `DIRECT_LOG_API_KEY` in the `X-BlueOrch-Key` header. |

## End-to-end automation flow

```text
SIEM or Endpoint Agent → Normalize & Deduplicate → Incident → n8n V3 Claim
→ Remote MCP Evidence → Deep AI Investigation → Response Proposal
→ Human Approval → Simulated Response → Contained → Immutable Audit
```

The current V3 workflow polls durable incidents, invokes the authenticated MCP gateway, and creates
proposals only for usable high/critical true-positive investigations. Low/medium or uncertain results
remain with the analyst. Only BlueOrch's approval service can execute a proposal. The final report is
available from `GET /api/v1/incidents/{incident_id}/report`.

## Screenshots

The screenshots below were captured directly from the live production deployment after the verified
MCP V3 end-to-end run; they are not mockups or locally substituted dashboard images.

### SOC Command Center

![BlueOrch live SOC overview](docs/screenshots/blueorch-live-command-overview.jpg)

The live overview presents the SIEM → enrichment → AI triage → investigation → approval → response
pipeline alongside production incident telemetry, MCP/RAG integrations and the human approval rail.

### Live incident queue

![BlueOrch live incident queue](docs/screenshots/blueorch-live-incident-queue.jpg)

The incident queue is populated from backend telemetry and shows the verified MCP investigation tests,
severity, response state and endpoint source without static frontend counters.

### Security data sources — Splunk and Wazuh

![BlueOrch SIEM settings with Splunk and Wazuh](docs/screenshots/blueorch-live-siem-settings.jpg)

The Settings workspace supports encrypted Splunk Management API and Wazuh Indexer connections,
connection testing, TLS verification, index selection, manual synchronization, and a live SIEM signal.

### Direct logs — Windows collector

![BlueOrch direct log agent setup](docs/screenshots/blueorch-live-direct-log-settings.jpg)

The second ingestion mode registers a device-specific key and reports real online/offline state. The
dependency-free collector reads Windows Event Logs, sends authenticated HTTPS batches and heartbeats,
deduplicates by record ID, and retains an on-disk retry queue through network interruptions. Device
status is visible after the operator supplies the registration token; the token is never embedded in
screenshots or returned by the backend.

### Human approval centre

![BlueOrch live human approval centre](docs/screenshots/blueorch-live-approval-centre.jpg)

High-risk recommendations stop here. The system exposes the proposed action, target, evidence summary
and incident reference; only an analyst can approve or reject execution.

### Remote MCP tool audit

![BlueOrch MCP tool history](docs/screenshots/blueorch-live-mcp-history.jpg)

Every allowlisted call is timed and audited, including incident retrieval, related-incident search,
MITRE mapping, SOC runbook retrieval and response-proposal creation.

### Human-approved response and immutable audit

![BlueOrch contained incident audit trail](docs/screenshots/blueorch-live-audit-log.jpg)

The audit trail records proposal creation, analyst approval, simulated execution and the final
`contained` transition. No firewall, EDR or IAM action is represented as real in the current version.

### Production system health

![BlueOrch live production system health](docs/screenshots/blueorch-live-system-health.jpg)

The health view polls the real backend and confirms the production environment, database connectivity
and that demo mode is disabled.

> The interface is optimized for desktop security operations. Live provider features depend on the
> environment variables documented above; response actions remain intentionally simulated.

## License

Released under the [MIT License](LICENSE). You may use, modify, and distribute
the project provided that the original copyright and license notice are retained.

Copyright © 2026 Vasanth Kumar.
