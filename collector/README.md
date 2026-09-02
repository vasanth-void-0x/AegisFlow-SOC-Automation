# BlueOrch Windows Collector

The dependency-free collector continuously reads new Windows Event Log records, sends authenticated
heartbeats and batches, and retains unsent events on disk during network interruption.

## Requirements

- Windows 10/11 or Windows Server.
- Administrator PowerShell for installation.
- Python 3 available to the SYSTEM account.
- A persistent BlueOrch deployment with `DATABASE_URL` and `DIRECT_LOG_REGISTRATION_TOKEN` configured.
- A one-time device API key generated from **Settings → Direct Log Source**.

## Install

Open this directory in Administrator PowerShell:

```powershell
.\install_windows.ps1 `
  -ApiUrl "https://blueorch-soc-automation.vercel.app" `
  -ApiKey "boa_COPY_THE_ONE_TIME_DEVICE_KEY" `
  -SourceName "BLUEORCH-WIN-01" `
  -Profile "security"
```

Profiles:

| Profile | Channels |
|---|---|
| `security` | Windows Security |
| `system` | Security + System |
| `full` | Security + System + Application |

The installer stores configuration under `C:\ProgramData\BlueOrch\Agent` and creates the
`BlueOrch Log Agent` scheduled task running as SYSTEM at boot.

## Verify

```powershell
Get-ScheduledTask -TaskName "BlueOrch Log Agent" |
  Select-Object TaskName, State

Get-ScheduledTaskInfo -TaskName "BlueOrch Log Agent" |
  Select-Object LastRunTime, LastTaskResult
```

`LastTaskResult = 0` indicates the last task invocation completed successfully. BlueOrch marks an agent
online when a valid heartbeat or log batch was received within the last three minutes. Enter the
registration token in Settings to allow the dashboard to list the device status; do not use the device
API key for that administrative request.

## Restart

```powershell
Stop-ScheduledTask -TaskName "BlueOrch Log Agent"
Start-ScheduledTask -TaskName "BlueOrch Log Agent"
```

## Credential separation

| Credential | Used by | Header / environment |
|---|---|---|
| Device API key | Collector heartbeat and event batches | `X-BlueOrch-Agent-Key` |
| Registration token | Operator registering/listing devices | `X-BlueOrch-Registration-Token` |
| Direct-log API key | Generic direct ingestion endpoint | `X-BlueOrch-Key` |
| MCP gateway key | n8n/MCP tool execution | `X-BlueOrch-MCP-Key` |

These keys are not interchangeable. A device API key is displayed once; BlueOrch stores only its hash.

## Troubleshooting

| Symptom | Check |
|---|---|
| Agent appears offline | Confirm the scheduled task is running and `LastTaskResult`; verify system time and outbound HTTPS |
| `401 Invalid agent API key` | The config contains the wrong/revoked device key; register a new device key |
| `422 Unprocessable Entity` | Update the collector/config so its heartbeat or batch matches the current API schema |
| Events do not create incidents | Low-information events may be filtered; use a high-severity safe test event and inspect API response |
| Network unavailable | Check the retry queue under `C:\ProgramData\BlueOrch\Agent`; it is replayed after reconnection |

## Uninstall

```powershell
.\uninstall_windows.ps1
```

Remove or archive `C:\ProgramData\BlueOrch\Agent` separately only after confirming no queued events or
configuration are needed. The MVP does not yet expose remote key revocation in the UI; agent lifecycle
controls are part of the [production-ready pilot roadmap](../docs/ROADMAP.md).
