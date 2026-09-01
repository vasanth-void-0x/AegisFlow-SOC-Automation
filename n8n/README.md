# BlueOrch n8n Orchestration

## Recommended: incident-driven V2

Import **`blueorch-incident-automation-v2.json`** for the current BlueOrch
architecture. It does not accept raw endpoint logs. Agent, JSON webhook,
syslog, file, and SIEM inputs first create durable incidents in BlueOrch; the
workflow then polls the production API every 15 seconds and processes one new
incident at a time.

The V2 flow is:

1. Fetch the next incident with status `new`.
2. Claim it by changing its status to `triaging`.
3. Enrich its indicators and run Groq AI triage.
4. For a high/critical true positive with a valid response target, create a
   pending response proposal and move the incident to `pending_approval`.
5. Stop at the human approval gate. Approval or rejection happens only in the
   BlueOrch Approval Centre. Approval immediately invokes the backend's safe
   response adapter and records the execution in the audit timeline.

Because local n8n pulls from the public BlueOrch API, Vercel does not need to
reach `localhost:5678`, and no public n8n tunnel is required. If n8n is
offline, incidents remain safely stored with status `new` and are picked up
when n8n returns.

Import the workflow, publish it, and keep n8n running. `Manual Test` can be
used to process one waiting incident immediately.

## Legacy webhook workflow

Two workflows:

- **`blueorch-workflow.json`** - the main pipeline: webhook -> create incident ->
  dedup check -> enrich -> AI triage -> severity branch -> analyst task ->
  approval gate for high-risk actions -> status update -> audit record.
- **`blueorch-error-handler.json`** - linked as the main workflow's error
  workflow. Fires automatically if any node in the main workflow fails after
  its retries are exhausted, so a failed security-critical step is never
  silently swallowed.

## Import

1. In n8n: **Workflows -> Import from File** -> select `blueorch-error-handler.json` first (so the main workflow can reference it), then `blueorch-workflow.json`.
2. Open the main workflow's **Settings** and confirm "Error Workflow" points at
   "BlueOrch - Error Handler".

## BlueOrch API target

The importable cloud workflow is preconfigured for:

```
https://blueorch-soc-automation.vercel.app
```

Deploy BlueOrch at that address before activating the workflow. If the domain changes, update the
base URL in the seven HTTP Request nodes after import.

## Triggering the workflow

The workflow listens on:

```
POST http://<your-n8n-host>/webhook/blueorch-alert
```

Send it the same JSON body as `POST /api/v1/alerts` (see `sample-data/` for
examples). Example:

```bash
curl -X POST https://vasantth.app.n8n.cloud/webhook/blueorch-alert \
  -H "Content-Type: application/json" \
  -d @../sample-data/brute_force_ssh.json
```

For raw endpoint logs without a SIEM, send them directly to BlueOrch:

```bash
curl -X POST https://blueorch-soc-automation.vercel.app/api/v1/logs/ingest \
  -H "Content-Type: application/json" \
  -H "X-BlueOrch-Key: $DIRECT_LOG_API_KEY" \
  -d '{"message":"Failed login brute force from 203.0.113.10 to 10.0.0.5","source_type":"agent","source_name":"windows-lab","event_id":"test-001"}'
```

The included `collector/blueorch_agent.py` continuously reads new Windows Event Log records,
sends authenticated batches, heartbeats, and keeps a disk retry queue. The workflow remains
the automation entry for normalized SIEM alerts; both inputs create the same
canonical incident records and dashboard KPIs.

## What each branch does

| Severity (from AI triage) | Action |
|---|---|
| critical | Analyst task (P1) -> approval gate if `requires_human_approval` |
| high | Analyst task (P2) -> approval gate if `requires_human_approval` |
| medium | Analyst task (P3), no approval gate |
| low | Log only, no analyst task |

## Duplicate handling

If `POST /api/v1/alerts` returns `409` (duplicate/idempotent alert), the
workflow stops immediately at the "Is Duplicate Alert?" node - no incident is
re-processed, no duplicate analyst task is created.

## Retry policy

Every HTTP Request node has `retryOnFail: true` with 2-3 attempts and a
wait-between-tries delay, matching the enrichment/triage services' own
timeout and retry behavior on the backend side.

## Notes / limitations

- The "Create Analyst Task" and "Notify On-Call" nodes are left as `NoOp`
  placeholders - wire them to Slack/Jira/PagerDuty/etc. in your own n8n
  instance; this keeps the importable JSON free of environment-specific
  credentials.
- This workflow assumes the BlueOrch backend is reachable at the configured production URL. It
  does not manage backend deployment itself.
- Human approval and response execution are enforced by BlueOrch, never by a
  bypass node. After approval, the incident moves to `contained` and its final
  report is available at `/api/v1/incidents/{id}/report`.
