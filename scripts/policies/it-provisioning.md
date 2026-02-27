# IT Provisioning & Security Policy — Alex SaaS Inc

*Effective Date: January 1, 2026 | Version 2.8 | Policy Owner: VP of Engineering / IT*

## 1. Equipment Provisioning

### 1.1 Standard Equipment by Role

| Role Category | Laptop | Monitors | Peripherals | Budget |
|---------------|--------|----------|-------------|--------|
| Engineering (IC) | MacBook Pro 16" M4 Pro (36GB RAM) | 2× 27" 4K | Mechanical keyboard, ergonomic mouse | $4,500 |
| Engineering (Manager+) | MacBook Pro 16" M4 Max (48GB RAM) | 2× 27" 4K | Full desk setup | $5,500 |
| Design / Creative | MacBook Pro 16" M4 Max (48GB RAM) | 1× 32" 5K + 1× 27" 4K | Wacom tablet, calibrated display | $6,000 |
| Sales / Marketing | MacBook Air 15" M4 (24GB RAM) | 1× 27" 4K | Standard peripherals | $3,000 |
| Finance / HR / Ops | MacBook Air 15" M4 (24GB RAM) | 1× 27" 4K | Standard peripherals | $3,000 |
| Executive (VP+) | MacBook Pro 16" M4 Pro (36GB RAM) | 2× 27" 4K | Premium desk setup | $5,500 |
| Intern / Contractor | MacBook Air 13" M4 (16GB RAM) | 1× 24" 4K | Basic peripherals | $2,000 |

### 1.2 Provisioning Timeline
- **Day -5 (before start):** IT receives new hire notification from HR system.
- **Day -3:** Laptop ordered/prepared, accounts created, access provisioned.
- **Day -1:** Equipment shipped (remote) or placed at desk (office).
- **Day 1:** New hire completes device enrollment (MDM) + security training.
- Monitors and peripherals ship within 5 business days of start.

### 1.3 Equipment Refresh Cycle
- Laptops: replaced every 3 years or upon hardware failure.
- Monitors: replaced every 5 years.
- Peripherals: replaced as needed (submit IT ticket).
- Early refresh for role change requiring different spec (e.g., moving to Engineering).

## 2. Software Licenses

### 2.1 Universal (All Employees)
- Google Workspace (email, docs, drive, calendar)
- Slack (Business+)
- Zoom (Pro)
- 1Password (Teams)
- Notion (team workspace)
- Okta SSO (identity provider)

### 2.2 Role-Specific Licenses

| Department | Software | License Type |
|-----------|----------|-------------|
| Engineering | GitHub Enterprise, JetBrains All Products, Linear, Datadog, AWS/GCP console | Team |
| Design | Figma (Professional), Adobe Creative Cloud | Individual |
| Sales | Salesforce, Gong, Outreach, LinkedIn Sales Navigator | Seat |
| Marketing | HubSpot, Canva Pro, Google Ads, SEMrush | Team |
| Finance | QuickBooks, Expensify, Stripe Dashboard, Carta | Seat |
| HR | BambooHR, Greenhouse, Lattice | Admin |
| Legal | DocuSign, Ironclad | Seat |
| All Managers | Lattice (performance), Culture Amp (engagement) | Seat |

### 2.3 License Request Process
- Standard licenses (listed above): auto-provisioned based on role.
- Non-standard software: submit request via IT portal → manager approval → IT review → procurement.
- Maximum 5 business days for license procurement; 24-hour SLA for standard provisioning.

## 3. Access Levels by Role

### 3.1 Access Tiers

| Tier | Access Level | Roles | Approval |
|------|-------------|-------|----------|
| Tier 1 — Basic | Email, Slack, Notion, PTO system | All employees | Auto |
| Tier 2 — Department | Department shared drives, team tools | Department members | Auto |
| Tier 3 — Sensitive | Customer data, financial systems, HR data | Specific roles | Manager + Data Owner |
| Tier 4 — Production | Production infrastructure, databases, CI/CD | Engineering L5+ | Eng Director + Security |
| Tier 5 — Admin | IAM, billing, security tooling, audit logs | IT/Security team | VP Engineering + CISO |

### 3.2 Production Access Rules
- **Read-only production access:** L4+ engineers, requires on-call training completion.
- **Write production access:** L5+ engineers, requires incident response certification.
- **Database admin access:** Staff+ engineers + DBA, requires additional background check.
- All production access logged and audited quarterly.
- Break-glass procedure: emergency access via PagerDuty → auto-revoke after 4 hours.

### 3.3 Access Review Cadence
- Quarterly: automated review of all Tier 3+ access.
- On role change: immediate access adjustment (add new, revoke old within 24 hours).
- On termination: all access revoked within 1 hour of HR notification.

## 4. Security Requirements

### 4.1 Device Security (Mandatory)
- **MDM enrollment:** All company devices enrolled in Jamf (macOS) or Intune (Windows).
- **Full disk encryption:** FileVault (macOS) or BitLocker (Windows) — enforced via MDM.
- **Firewall:** Enabled, no exceptions.
- **Auto-updates:** OS and critical software updates applied within 72 hours of release.
- **Screen lock:** Auto-lock after 5 minutes of inactivity.
- **Antivirus:** CrowdStrike Falcon installed on all endpoints.

### 4.2 Authentication
- **SSO:** All applications must use Okta SSO. No standalone passwords for SaaS tools.
- **MFA:** Required on all accounts. Hardware key (YubiKey) required for Tier 4+ access.
- **Password policy:** Minimum 16 characters, complexity enforced by 1Password.
- **Session timeout:** 8 hours for standard apps, 1 hour for Tier 4+ systems.

### 4.3 Data Handling
- **Classification:** Public, Internal, Confidential, Restricted.
- **Confidential data** (customer PII, financial records): encrypted at rest + in transit, no personal devices, no external sharing without Legal approval.
- **Restricted data** (credentials, keys, health data): encrypted, access logged, quarterly audit.
- **No USB storage devices** — disabled via MDM policy.
- **Personal device (BYOD):** Email and Slack only, via Okta Verify container. No code repos or customer data.

### 4.4 Incident Reporting
- All security incidents reported within 1 hour via #security-incidents Slack channel or security@alexsaas.com.
- Phishing emails: forward to phishing@alexsaas.com, then delete.
- Lost/stolen device: report immediately → IT remote wipes within 30 minutes.

## 5. Offboarding IT Checklist

### 5.1 Immediate (Within 1 Hour of Termination)
- [ ] Revoke Okta SSO (disables all app access)
- [ ] Disable email forwarding
- [ ] Revoke VPN access
- [ ] Remove from Slack workspaces
- [ ] Revoke GitHub/GitLab access
- [ ] Disable AWS/GCP IAM accounts

### 5.2 Within 24 Hours
- [ ] Recover company laptop and peripherals
- [ ] Transfer ownership of shared documents/drives
- [ ] Remove from distribution lists and shared calendars
- [ ] Archive email account (retained 7 years for compliance)
- [ ] Revoke all software licenses

### 5.3 Within 5 Business Days
- [ ] Confirm all equipment returned
- [ ] Final access audit (verify zero active sessions)
- [ ] Close IT tickets associated with departing employee
- [ ] Update org chart and directory
