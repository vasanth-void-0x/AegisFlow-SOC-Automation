# BlueOrch n8n Orchestration

Two workflows:

- **`aegisflow-workflow.json`** - the main pipeline: webhook -> create incident ->
  dedup check -> enrich -> AI triage -> severity branch -> analyst task ->
  approval gate for high-risk actions -> status update -> audit record.
- **`aegisflow-error-handler.json`** - linked as the main workflow's error
  workflow. Fires automatically if any node in the main workflow fails after
  its retries are exhausted, so a failed security-critical step is never
  silently swallowed.

## Import

1. In n8n: **Workflows -> Import from File** -> select `aegisflow-error-handler.json` first (so the main workflow can reference it), then `aegisflow-workflow.json`.
2. Open the main workflow's **Settings** and confirm "Error Workflow" points at
   "BlueOrch - Error Handler".

## Required environment variable

Set this in n8n (Settings -> Environment Variables, or your n8n `.env`):

```
AEGISFLOW_API_BASE=http://localhost:8000
```

## Triggering the workflow

The workflow listens on:

```
POST http://<your-n8n-host>/webhook/aegisflow-alert
```

Send it the same JSON body as `POST /api/v1/alerts` (see `sample-data/` for
examples). Example:

```bash
curl -X POST http://localhost:5678/webhook/aegisflow-alert \
  -H "Content-Type: application/json" \
  -d @../sample-data/brute_force_ssh.json
```

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
- This workflow assumes the BlueOrch backend is reachable at
  `AEGISFLOW_API_BASE`. It does not manage backend deployment itself.
