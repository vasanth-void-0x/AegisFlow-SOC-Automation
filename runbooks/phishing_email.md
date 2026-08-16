---
title: Phishing Email Investigation & Response
category: initial_access
mitre_techniques: [T1566]
severity_guidance: medium
---

# Phishing Email

## Detection Criteria
- User-reported suspicious email
- Email gateway flags sender reputation, SPF/DKIM/DMARC failure, or known
  phishing kit URL patterns
- Links to credential-harvesting pages or malicious attachments

## Investigation Steps
1. Review the email headers - sender domain, SPF/DKIM/DMARC results, reply-to
   mismatch.
2. Extract and enrich any URLs or attachment hashes against threat intelligence.
3. Check if any recipients clicked the link or opened the attachment (mail
   gateway/EDR telemetry).
4. If credentials may have been entered on a harvesting page, check for
   subsequent anomalous login activity on the affected account(s).
5. Determine the blast radius - how many users received the same email.

## Classification Guidance
- **True positive** if: sender domain/URL is confirmed malicious or matches a
  known phishing campaign pattern, or authentication anomalies follow a click.
- **False positive** if: a legitimate marketing/vendor email tripped a
  heuristic filter with no malicious link or attachment present.

## Recommended Response Actions (require human approval)
- Purge the email from all recipient mailboxes.
- Block the sender domain and any malicious URLs at the email gateway/proxy.
- Force password reset for any user who entered credentials on a harvesting page.
- Notify affected users and provide phishing awareness guidance.

## Notes
- Track recurring phishing campaigns by sender infrastructure/URL patterns to
  identify targeted attacks against the organization.
