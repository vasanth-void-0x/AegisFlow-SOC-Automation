---
title: Suspicious PowerShell Activity Investigation & Response
category: execution
mitre_techniques: [T1059.001]
severity_guidance: high
---

# Suspicious PowerShell Activity

## Detection Criteria
- Encoded command execution (`-enc`, `-EncodedCommand`)
- Download cradles (`IEX (New-Object Net.WebClient).DownloadString(...)`)
- Execution policy bypass (`-ExecutionPolicy Bypass`)
- Obfuscated or heavily concatenated command strings
- PowerShell spawned by an unusual parent process (e.g. Office apps, browsers)

## Investigation Steps
1. Decode any Base64-encoded command blocks to inspect the actual payload.
2. Identify the parent process. PowerShell launched from Word/Excel/Outlook or a
   browser is a strong indicator of a malicious macro or drive-by download.
3. Check for outbound network connections initiated by the PowerShell process
   shortly after execution.
4. Check the hash of any downloaded file against threat intelligence.
5. Review command-line history on the host for related activity (persistence
   mechanisms, scheduled tasks, registry run keys).

## Classification Guidance
- **True positive** if: encoded/obfuscated command combined with an unusual
  parent process or outbound connection to an unrecognized/flagged destination.
- **False positive** if: the command matches a known, approved admin script or
  a legitimate software deployment tool (e.g. SCCM, Intune) with a documented
  encoded-command pattern.

## Recommended Response Actions (require human approval)
- Isolate the affected host from the network (simulated in this system).
- Kill the malicious PowerShell process tree.
- Collect a memory/process snapshot before isolation if forensics is required.
- Block any C2 domain/IP identified during investigation.

## Notes
- PowerShell Script Block Logging (Event ID 4104) provides the decoded command
  content and should be enabled fleet-wide where possible.
