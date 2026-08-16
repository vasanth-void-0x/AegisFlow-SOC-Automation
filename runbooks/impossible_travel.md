---
title: Impossible Travel Investigation & Response
category: defense_evasion
mitre_techniques: [T1078]
severity_guidance: medium
---

# Impossible Travel

## Detection Criteria
- Two successful logins for the same account from geographically distant
  locations within a time window that makes physical travel impossible
- Often surfaced by identity providers (Azure AD, Okta) as a native risk signal

## Investigation Steps
1. Confirm both login locations and the time delta between them.
2. Check whether either location corresponds to a known VPN/proxy exit node
   or corporate VPN egress point (common false-positive source).
3. Review the authentication method used for each login (password only vs MFA).
4. Check for any suspicious activity following the second login - mailbox rule
   changes, data downloads, privilege changes.
5. Contact the user directly if feasible to confirm legitimate travel or VPN use.

## Classification Guidance
- **True positive** if: neither location matches known VPN infrastructure, MFA
  was not enforced or was bypassed, and suspicious post-login activity occurred.
- **False positive** if: one location matches a corporate VPN exit node, or the
  user confirms legitimate travel/VPN usage.

## Recommended Response Actions (require human approval)
- Force a password reset and revoke active sessions for the account.
- Require re-enrollment in MFA.
- Review and revert any mailbox rules or permission changes made during the
  suspicious session.

## Notes
- Tune impossible-travel detection thresholds to account for your
  organization's known VPN egress locations to reduce false positives.
