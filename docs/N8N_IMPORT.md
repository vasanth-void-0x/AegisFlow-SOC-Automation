# n8n Import Guide

The full n8n setup, import steps, and workflow explanation live in
[`n8n/README.md`](../n8n/README.md) next to the workflow JSON files themselves, so they stay in sync as
the workflow evolves.

Quick reference (recommended incident-driven workflow):

1. Run n8n: `docker run -it --rm -p 5678:5678 n8nio/n8n` (or use the `n8n` service in
   `docker-compose.yml`).
2. Import `n8n/blueorch-incident-automation-v2.json`.
3. Publish the workflow. It polls the production BlueOrch API every 15 seconds;
   no inbound webhook or public tunnel is required.
4. Create an incident through any BlueOrch input. The workflow performs
   enrichment and AI triage, then creates a proposal for qualifying incidents.
5. Approve or reject the proposal in BlueOrch Approval Centre. Only an explicit
   human approval executes the safe response adapter.

See [`n8n/README.md`](../n8n/README.md) for the full workflow architecture (severity branching, retry
policy, error workflow, approval gate).
