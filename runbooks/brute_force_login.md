---
title: Brute Force Login Investigation & Response
category: credential_access
mitre_techniques: [T1110]
severity_guidance: high
---

# Brute Force Login

## Detection Criteria
- Multiple failed authentication attempts (typically 5+) against a single account or host
- Attempts originate from one or a small number of source IPs within a short window
- Applies to SSH, RDP, VPN, web application login forms, and API authentication endpoints

## Investigation Steps
1. Confirm the failure count and time window from the source log (SIEM/EDR).
2. Check whether the source IP is public or internal. Internal sources may indicate
   a compromised host rather than an external attacker.
3. Enrich the source IP against threat intelligence (reputation, known scanning
   infrastructure, prior abuse reports).
4. Determine if any attempt in the sequence succeeded. A successful login following
   a failure burst is a strong true-positive indicator.
5. Check the targeted account's recent activity for anomalies (new device, new
   location, privilege escalation) if any login succeeded.
6. Review whether the account has MFA enabled.

## Classification Guidance
- **True positive** if: high volume of failures from a single external IP, and/or
  a successful login follows the failure burst with no legitimate explanation.
- **False positive** if: failures come from a known internal service account
  misconfiguration, a scheduled job with stale credentials, or a known scanner
  under an approved pentest window.

## Recommended Response Actions (require human approval)
- Block the offending source IP at the perimeter/firewall (simulated in this system).
- Force a password reset and session invalidation for the targeted account if any
  login succeeded.
- Enable/verify MFA on the targeted account.
- Notify the account owner.

## Notes
- Rate-limiting and account lockout policies reduce brute-force risk but should not
  be the only control - always investigate lockout events for account-enumeration
  patterns.
