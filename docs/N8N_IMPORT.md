# n8n Import Guide

The full n8n setup, import steps, and workflow explanation live in
[`n8n/README.md`](../n8n/README.md) next to the workflow JSON files themselves, so they stay in sync as
the workflow evolves.

Quick reference (recommended incident-driven workflow):

1. Run n8n: `docker run -it --rm -p 5678:5678 n8nio/n8n` (or use the `n8n` service in
   `docker-compose.yml`).
2. Set `BLUEORCH_MCP_KEY` in the environment that starts n8n. Its value must
   exactly match the backend's `MCP_GATEWAY_API_KEY`.
   For local n8n nodes that read `$env`, also set `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, then fully
   restart the n8n process. Prefer an n8n credential/secret store when your deployment supports it.
3. Import `n8n/blueorch-incident-automation-v3.json`. The imported workflow title is
   **BlueOrch - MCP Deep Investigation V3.1 RBAC Fix**.
4. Publish the workflow. It polls the production BlueOrch API every 15 seconds;
   no inbound webhook or public tunnel is required.
5. Create an incident through any BlueOrch input. The workflow invokes the
   authenticated MCP investigation gateway, live VirusTotal enrichment, MITRE
   mapping, runbook retrieval, historical correlation, and deep AI analysis.
6. Approve or reject the proposal in BlueOrch Approval Centre. Only an explicit
   human approval executes the current safe simulated-response adapter; no real EDR/firewall/IAM action
   is claimed by the MVP.

See [`n8n/README.md`](../n8n/README.md) for the full workflow architecture (severity branching, retry
policy, error workflow, approval gate).
