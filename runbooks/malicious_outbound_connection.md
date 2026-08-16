---
title: Malicious Outbound Connection Investigation & Response
category: command_and_control
mitre_techniques: [T1071]
severity_guidance: high
---

# Malicious Outbound Connection

## Detection Criteria
- Outbound connection from an internal host to a destination flagged as
  malicious (C2 infrastructure, known botnet, malicious hosting) by threat intel
- Beaconing pattern - periodic connections at regular intervals to the same
  destination
- Connection over an unusual port or protocol mismatch (e.g. HTTP traffic on a
  non-standard port)

## Investigation Steps
1. Enrich the destination IP/domain against threat intelligence.
2. Identify the process on the source host that initiated the connection.
3. Check for a beaconing pattern - regular interval connections over time.
4. Determine what data, if any, was transferred (volume, direction).
5. Check if the source host shows other compromise indicators (unusual
   processes, persistence mechanisms, recent suspicious logins).

## Classification Guidance
- **True positive** if: destination is confirmed malicious/C2 infrastructure
  and/or a clear beaconing pattern exists with no legitimate business reason.
- **False positive** if: destination is a legitimate but newly-categorized
  service, CDN, or SaaS endpoint that triggered an overly broad threat intel
  feed entry.

## Recommended Response Actions (require human approval)
- Block the destination IP/domain at the firewall/proxy (simulated in this system).
- Isolate the source host from the network pending full investigation.
- Identify and remove the process/persistence mechanism responsible for the
  outbound traffic.
- Hunt for the same destination across other hosts in the environment.

## Notes
- Correlate outbound connection alerts with DNS query logs to identify the
  full chain (domain resolution -> connection) for more complete evidence.
