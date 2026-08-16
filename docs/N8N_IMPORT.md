# n8n Import Guide

The full n8n setup, import steps, and workflow explanation live in
[`n8n/README.md`](../n8n/README.md) next to the workflow JSON files themselves, so they stay in sync as
the workflow evolves.

Quick reference:

1. Run n8n: `docker run -it --rm -p 5678:5678 n8nio/n8n` (or use the `n8n` service in
   `docker-compose.yml`).
2. Import `n8n/aegisflow-error-handler.json` first, then `n8n/aegisflow-workflow.json`.
3. Set the `AEGISFLOW_API_BASE` environment variable in n8n to point at your running backend
   (e.g. `http://localhost:8000` for local dev, or `http://backend:8000` inside Docker Compose).
4. Trigger the workflow by POSTing an alert to its webhook — see `n8n/README.md` for the exact URL and
   a working `curl` example, and `sample-data/` for example alert payloads.

See [`n8n/README.md`](../n8n/README.md) for the full workflow architecture (severity branching, retry
policy, error workflow, approval gate).
