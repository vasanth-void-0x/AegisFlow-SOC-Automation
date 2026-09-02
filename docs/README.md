# BlueOrch Documentation

BlueOrch documentation is organized by task so the root README can stay focused on the product story.

## Start here

| Goal | Document |
|---|---|
| Understand the complete platform | [Architecture](ARCHITECTURE.md) |
| Run the application locally | [Root quick start](../README.md#quick-start-local-no-docker) |
| Configure all secrets | [Environment variables](../README.md#environment-variables) |
| Connect n8n V3.1 | [n8n workflow guide](../n8n/README.md) |
| Connect an MCP client | [MCP setup](MCP_SETUP.md) |
| Install the Windows collector | [Collector guide](../collector/README.md) |
| Understand current vs future scope | [Production roadmap](ROADMAP.md) |
| Diagnose a failure | [Troubleshooting](../README.md#troubleshooting) |

## Evidence and assurance

- Live production screenshots are stored in [`docs/screenshots`](screenshots/).
- Backend security and integration tests are in [`backend/tests`](../backend/tests/).
- AI evaluation inputs and the latest report are in [`evaluation`](../evaluation/).
- n8n importable workflows are versioned beside their guide in [`n8n`](../n8n/).
- RAG source runbooks are versioned in [`runbooks`](../runbooks/).

## Documentation principles

1. Current, simulated, provider-dependent, and planned capabilities are labelled separately.
2. Secrets shown in examples are placeholders; real keys must never be committed.
3. A response proposal is not described as an executed real-world action.
4. Enterprise capabilities are roadmap items, not MVP claims.
