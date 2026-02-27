"""Senso policy search helper — wraps raw search with local policy fallback + self-improvement.

The self-improvement loop:
1. Agents query policies → get results from Senso OR local store
2. Human overrides a decision → LEARNED edge in Neo4j
3. Self-improvement cron detects pattern (3+ overrides) → generates new policy
4. New policy saved to local store + uploaded to Senso (when available)
5. Next agent query → gets updated policy → makes better decision
"""

import json
from pathlib import Path
from integrations.senso import senso_client


# Local policy store — persists across requests, updated by self-improvement cron
POLICY_STORE: dict[str, dict] = {}

# Pre-populated AlexSaaS company policies
DEFAULT_POLICIES = {
    "salary_bands": {
        "category": "hr",
        "title": "AlexSaaS Salary Bands",
        "content": """SALARY BANDS BY ROLE AND LOCATION:

Senior Engineer:
- San Francisco: $170,000 - $210,000 (target: $190,000)
- New York: $165,000 - $200,000 (target: $182,000)
- Austin: $145,000 - $180,000 (target: $162,000)
- Remote: $140,000 - $175,000 (target: $157,000)

Engineering Director:
- San Francisco: $220,000 - $280,000 (target: $250,000)
- New York: $210,000 - $270,000 (target: $240,000)
- Austin: $190,000 - $240,000 (target: $215,000)

Product Designer:
- San Francisco: $150,000 - $190,000 (target: $170,000)
- New York: $145,000 - $185,000 (target: $165,000)

Product Manager:
- San Francisco: $160,000 - $200,000 (target: $180,000)
- New York: $155,000 - $195,000 (target: $175,000)

COMPENSATION RULES:
1. All offers must be within the defined salary band for the role and location
2. Offers below the 25th percentile require VP approval
3. Offers above the 75th percentile require C-suite approval
4. Cost-of-living adjustments apply when relocating between offices
5. Equity grants: Senior IC = 0.05-0.1%, Director = 0.1-0.25%, VP+ = 0.25-0.5%
6. Signing bonuses: Up to 15% of base salary for senior roles
7. Annual merit increase: 3-8% based on performance rating"""
    },
    "benefits_policy": {
        "category": "hr",
        "title": "AlexSaaS Benefits Policy",
        "content": """EMPLOYEE BENEFITS:
- Health insurance: 100% employee coverage, 80% dependents (Blue Shield PPO)
- Dental & Vision: 100% employee coverage
- 401k: 4% employer match, immediate vesting
- PTO: 20 days + 10 company holidays + unlimited sick days
- Parental leave: 16 weeks paid (birth + non-birth parents)
- Education budget: $5,000/year for courses, conferences, books
- Equipment budget: $3,000 for new hires (laptop, monitor, peripherals)
- Remote work stipend: $150/month for internet + home office
- Commuter benefits: Pre-tax transit up to $300/month
- Wellness: $100/month gym/fitness reimbursement"""
    },
    "compliance_checklist": {
        "category": "compliance",
        "title": "AlexSaaS New Hire Compliance Checklist",
        "content": """NEW HIRE COMPLIANCE REQUIREMENTS:
1. Background check (completed before start date)
2. I-9 Employment Eligibility Verification (within 3 business days)
3. W-4 Federal Tax Withholding
4. State tax withholding forms
5. NDA and IP Assignment Agreement
6. Employee Handbook acknowledgment
7. IT Security Policy acknowledgment
8. Anti-harassment training (within 30 days)
9. Data privacy training (within 30 days)

CALIFORNIA-SPECIFIC:
- Pay transparency: Salary range must be disclosed in job posting
- Sexual harassment prevention training: 2 hours within 6 months
- Notice to Employee (Labor Code Section 2810.5)

NEW YORK-SPECIFIC:
- NY Paid Family Leave notice
- Sexual harassment prevention training: Annual
- Freelance Isn't Free Act compliance (if applicable)"""
    },
    "onboarding_process": {
        "category": "it",
        "title": "AlexSaaS IT Onboarding Process",
        "content": """IT ONBOARDING CHECKLIST:
1. Create Google Workspace account (email, calendar, drive)
2. Provision Slack account + add to department channels
3. Create GitHub account + add to org + team repos
4. Create Jira account + add to department board
5. Provision Okta SSO (all apps via single sign-on)
6. Order equipment (MacBook Pro M4, monitor, peripherals)
7. Set up VPN access (for production systems, engineering only)
8. Create AWS IAM user (engineering only, least-privilege)
9. Schedule IT orientation (security policies, MFA setup)
10. Add to on-call rotation (after 30-day ramp, engineering only)

EQUIPMENT STANDARDS:
- Engineering: MacBook Pro M4 14", 36GB RAM, 1TB SSD
- Non-engineering: MacBook Air M4, 16GB RAM, 512GB SSD
- Monitor: LG 27" 4K (optional second monitor for engineering)
- All laptops enrolled in MDM (Jamf) before distribution"""
    },
    "expense_policy": {
        "category": "finance",
        "title": "AlexSaaS Expense & Travel Policy",
        "content": """EXPENSE POLICY:
- Meals: Up to $75/day for business travel
- Hotels: Up to $250/night (major cities $350)
- Flights: Economy for <4 hours, Business for 4+ hours
- Client entertainment: Up to $150/person, pre-approval >$500
- Software/tools: Up to $50/month self-serve, >$50 requires manager approval
- Team events: Up to $100/person/quarter

APPROVAL THRESHOLDS:
- <$500: Self-approved (submit receipt)
- $500-$2,000: Manager approval
- $2,000-$10,000: Director approval
- >$10,000: VP/C-suite approval

CORPORATE CARD:
- Issued to directors and above
- All charges must have receipts within 5 business days
- Personal use prohibited — immediate termination"""
    }
}


def _init_policies():
    """Initialize policy store with defaults."""
    if not POLICY_STORE:
        POLICY_STORE.update(DEFAULT_POLICIES)


# Policy category mapping for routing queries to the right context
POLICY_CATEGORIES = {
    "hr": {
        "keywords": [
            "salary", "compensation", "hire", "hiring", "termination", "pip",
            "performance", "benefits", "pto", "leave", "parental", "bonus",
            "equity", "stock", "onboarding", "offboarding", "interview",
            "promotion", "level", "band", "401k", "insurance", "health",
        ],
        "description": "HR & People policies — salary bands, benefits, hiring process",
    },
    "it": {
        "keywords": [
            "laptop", "equipment", "provisioning", "software", "license",
            "access", "security", "mdm", "okta", "sso", "mfa", "device",
            "monitor", "vpn", "github", "aws", "offboarding",
        ],
        "description": "IT provisioning — equipment, software, access levels",
    },
    "finance": {
        "keywords": [
            "expense", "budget", "travel", "reimbursement", "approval",
            "purchase", "vendor", "card", "corporate", "hotel", "flight",
            "per diem", "receipt", "spending",
        ],
        "description": "Finance — expense limits, travel policy, approvals",
    },
    "compliance": {
        "keywords": [
            "i-9", "i9", "background check", "nda", "ip", "intellectual property",
            "compliance", "regulation", "california", "new york", "harassment",
            "onboarding checklist", "w-4", "tax",
        ],
        "description": "Compliance — I-9, background checks, NDA, state requirements",
    },
}


def detect_policy_category(query: str) -> list[str]:
    """Detect which policy categories a query relates to."""
    query_lower = query.lower()
    matches = []
    for category, info in POLICY_CATEGORIES.items():
        if any(kw in query_lower for kw in info["keywords"]):
            matches.append(category)
    return matches or ["hr", "compliance"]


async def search_policies(query: str, top_k: int = 5) -> dict:
    """Search policies — tries Senso first, falls back to local policy store."""
    _init_policies()
    categories = detect_policy_category(query)

    # Try Senso first
    senso_results = []
    try:
        raw = await senso_client.search_policy(query, top_k=top_k)
        senso_results = raw.get("results", raw.get("data", []))
        if isinstance(raw, list):
            senso_results = raw
    except Exception:
        pass

    # Search local policy store (always — to supplement Senso)
    local_results = []
    query_lower = query.lower()
    for key, policy in POLICY_STORE.items():
        # Match by category or keyword presence in content
        if policy["category"] in categories or any(
            word in policy["content"].lower() for word in query_lower.split() if len(word) > 3
        ):
            local_results.append({
                "source": "local_policy_store",
                "key": key,
                "title": policy["title"],
                "content": policy["content"],
                "category": policy["category"],
                "is_learned": policy.get("learned", False),
            })

    # Combine results (Senso first, then local)
    all_results = senso_results + local_results

    # Build context summary
    if all_results:
        snippets = []
        for r in all_results[:3]:
            text = r.get("content", r.get("text", r.get("snippet", str(r))))
            snippets.append(text[:500])
        context_summary = "\n---\n".join(snippets)
    else:
        context_summary = f"No policy results found for: {query}. Categories searched: {', '.join(categories)}"

    return {
        "query": query,
        "categories": categories,
        "results": all_results,
        "total_results": len(all_results),
        "senso_results": len(senso_results),
        "local_results": len(local_results),
        "context_summary": context_summary,
    }


def add_learned_policy(field: str, new_value: str, reason: str, override_count: int):
    """Add a learned policy from self-improvement cron.
    
    This is the key self-improvement mechanism:
    - Human overrides a decision 3+ times in the same direction
    - Self-improvement cron detects the pattern
    - Calls this function to update the policy store
    - Next time an agent queries, they get the updated policy
    """
    key = f"learned_{field}_{len(POLICY_STORE)}"
    POLICY_STORE[key] = {
        "category": "hr",
        "title": f"LEARNED POLICY: {field} adjustment",
        "content": (
            f"AUTO-LEARNED POLICY (from {override_count} human overrides):\n"
            f"Field: {field}\n"
            f"Updated value: {new_value}\n"
            f"Reason: {reason}\n\n"
            f"This policy was automatically generated by the self-improvement engine "
            f"after detecting a consistent pattern of human corrections."
        ),
        "learned": True,
    }
    return key


async def is_policy_question(message: str) -> bool:
    """Check if a message is likely a policy-related question."""
    policy_signals = [
        "policy", "salary", "band", "benefit", "pto", "leave",
        "expense", "travel", "reimburs", "approval", "threshold",
        "compliance", "i-9", "background", "nda", "ip assignment",
        "equipment", "laptop", "access", "provision", "security",
        "what is our", "what's our", "what are the", "how much",
        "am i allowed", "can i", "do we", "is there a",
        "what's the limit", "what is the limit", "who approves",
    ]
    msg_lower = message.lower()
    return any(signal in msg_lower for signal in policy_signals)
