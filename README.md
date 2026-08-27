# AegisFlow — SOC Investigation & Response Automation Platform

[![Live](https://img.shields.io/badge/LIVE-SOC%20DASHBOARD-28d7f2?style=for-the-badge&logo=vercel&logoColor=white)](https://aegisflow-soc-automation.vercel.app/)
[![React](https://img.shields.io/badge/React-TypeScript-087ea4?style=flat-square&logo=react)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)](backend/)
[![Tests](https://img.shields.io/badge/Backend%20Tests-110%20Passing-3ecf8e?style=flat-square)](#testing)

### [Launch the live SOC dashboard →](https://aegisflow-soc-automation.vercel.app/)

![AegisFlow SOC Command Center](docs/screenshots/aegisflow-command-center.jpg)

AegisFlow is a working, end-to-end SOC (Security Operations Center) automation platform. It ingests
security alerts, enriches indicators of compromise, runs structured LLM-based triage, retrieves relevant
SOC runbooks with RAG, exposes its security tools through MCP, orchestrates the investigation with n8n,
and requires human approval before any response action executes.

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

**110 backend tests passing** (95 in the main FastAPI test suite + 15 in the isolated MCP server suite).

## Architecture

```mermaid
flowchart TB
    subgraph Ingestion
        A[Alert Source<br/>SIEM/EDR/Webhook] -->|POST /api/v1/alerts| B[FastAPI Backend]
    end

    subgraph Backend["Backend (FastAPI + SQLAlchemy + SQLite)"]
        B --> C[Incident Store]
        C --> D[Threat-Intel Enrichment<br/>VirusTotal + GeoIP + MITRE]
        D --> E[AI Triage<br/>Groq structured JSON]
        F[RAG Retriever<br/>SOC Runbooks] --> E
        E --> G[Response Proposal<br/>pending approval]
        G --> H[Human Approval API]
        H --> I[Simulated Response<br/>block_ip / isolate_host]
        C --> J[Immutable Timeline]
    end

    subgraph MCP["MCP Security Server (isolated process)"]
        K[7 typed tools] --> C
        K --> D
        K --> F
        K --> G
    end

    subgraph Orchestration
        L[n8n Workflow] -->|webhook| B
        L --> D
        L --> E
        L --> H
    end

    M[React Dashboard] -->|REST| B
    N[MCP Client<br/>e.g. Claude Desktop] --> K
```

## Repository structure

```text
aegisflow/
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
│   ├── tests/                    110 tests
│   ├── requirements.txt           Main backend deps
│   └── requirements-mcp.txt        Isolated MCP server deps (see below)
├── frontend/                React + TypeScript + Vite SOC dashboard
├── n8n/                      Importable workflow JSON + error handler
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

Visit `http://localhost:8000/health` — you should see `{"status": "ok", ...}`.
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

Then import `n8n/aegisflow-workflow.json` and `n8n/aegisflow-error-handler.json`. See
[docs/N8N_IMPORT.md](docs/N8N_IMPORT.md).

## Environment variables

See [.env.example](.env.example) for the full reference. Everything defaults to safe demo values —
**zero API keys are required to run the system.**

| Variable | Purpose | Required? |
|---|---|---|
| `GROQ_API_KEY` | Live AI triage | No — falls back to rule-based triage |
| `VIRUSTOTAL_API_KEY` | Live IOC reputation | No — falls back to demo enrichment |
| `ENABLE_REAL_RESPONSE_ADAPTER` | Enable real (non-simulated) response actions | No — **must stay `false` unless you've implemented and reviewed a real adapter** |
| `DATABASE_URL` | SQLite by default, Postgres-compatible | No |

## Testing

```bash
cd backend
pytest tests/ --ignore=tests/test_mcp_server.py -v   # 95 tests, main venv

# MCP server tests (separate venv):
pytest tests/test_mcp_server.py -v -o asyncio_mode=auto   # 15 tests, .venv-mcp
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
- Unauthorized/duplicate response actions — every response proposal requires human approval; approved
  proposals cannot be re-approved; rejected/expired proposals cannot execute.
- Oversized payloads / malformed JSON — request size limits and structured 422/413 handling.
- Rate limiting — per-IP sliding window middleware (configurable, default 120 req/min).

**Explicitly out of scope for this portfolio build:**
- Authentication/authorization (no user accounts, RBAC, or API auth — anyone with network access to the
  API can call it). A production deployment needs an auth layer in front of this.
- Multi-tenant isolation.
- Encryption at rest for the SQLite database.
- The `ENABLE_REAL_RESPONSE_ADAPTER` flag exists but no real adapter is implemented — response actions
  are always simulated in this repository, by design.

## Known limitations & honest notes

- **No live Groq/VirusTotal keys were used during development in this sandboxed environment** — those
  provider domains aren't reachable from the build environment's network policy. The live-API code paths
  are fully implemented and unit-tested with mocked HTTP responses, but have not been exercised against
  the real Groq/VirusTotal APIs. Bring your own keys locally to use them.
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
| n8n workflow can't reach the backend | If running n8n via Docker Compose, use `http://backend:8000` (the service name), not `localhost`, as `AEGISFLOW_API_BASE`. |
| `409 Conflict` on alert ingestion | Expected — this is the dedup/idempotency protection working. Check the `X-Existing-Incident-Id` response header for the existing incident. |

## Screenshots

### SOC Command Center

![AegisFlow live SOC overview](docs/screenshots/aegisflow-command-center.jpg)

The live overview presents the SIEM → enrichment → AI triage → investigation → approval → response
pipeline alongside system readiness, incident telemetry, MCP/RAG integrations, and fixed SOC rails.

> The interface is optimized for desktop security operations. Live provider features depend on the
> environment variables documented above; response actions remain intentionally simulated.

## License

Portfolio project — no license restrictions on personal/educational use.
