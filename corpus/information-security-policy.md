# Helix Technologies - Information Security Policy

**Document ID:** SEC-001
**Version:** 2026.1
**Effective date:** January 1, 2026
**Owner:** Security Team

## 1. Purpose And Scope

This policy defines the security requirements that protect Helix systems and data. It applies
to all employees, contractors and anyone with access to Company systems.

## 2. Accounts And Authentication

- **Multi-factor authentication (MFA) is mandatory** on all company accounts, including
  email, single sign-on and the code repository.
- Passwords must be at least **14 characters** and are managed through the company password
  manager (1Password). Password reuse across systems is prohibited.
- Credentials must never be shared. Each person uses their own account.

## 3. Device Security

- All laptops must have **full-disk encryption enabled** (FileVault or BitLocker).
- Devices must lock automatically after **10 minutes** of inactivity.
- Operating systems and security patches must be installed within **14 days** of release.
  IT manages patching on company devices.
- Antivirus/endpoint protection provided by IT must remain enabled.

## 4. Network Security

- Use the **company VPN** when accessing internal systems over public or untrusted networks.
- Home Wi-Fi networks must use WPA2 or WPA3 encryption with a strong password.

## 5. Data Classification

Helix classifies data into four levels. Handling requirements increase with sensitivity.

| Level | Examples | Handling |
|-------|----------|----------|
| Public | Marketing materials, public docs | No restrictions |
| Internal | Internal wikis, most email | Share only inside Helix |
| Confidential | Customer data, financials | Need-to-know; encrypt in transit |
| Restricted | Secrets, credentials, PII at scale | Strict need-to-know; access logged |

## 6. Acceptable Use

Use of company systems is governed by the Acceptable Use Policy (SEC-002).

## 7. Phishing And Incident Reporting

- Report suspected phishing or any security incident **immediately** to
  **security@helixtech.example** or via the "Report Phishing" button in email.
- Do not attempt to investigate a suspected compromise yourself; preserve evidence and let
  the Security Team respond.
- Helix runs periodic phishing simulations as part of security awareness.

## 8. Security Awareness Training

All employees must complete **Security Awareness training within their first 7 days** and
**annually thereafter**. Completion is tracked by the Security Team.

## 9. Third-Party Software

Installing third-party software or browser extensions that access company data requires
review. Submit requests to the Security Team. Use of unapproved AI tools with confidential
data is prohibited (see SEC-002).

## 10. Consequences

Violations of this policy may result in disciplinary action up to and including termination,
and may be reported to authorities where required by law.

## 11. Contact

Reach the Security Team at **security@helixtech.example**.
