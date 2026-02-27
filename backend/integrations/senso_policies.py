"""Senso policy search helper — wraps raw search with context enrichment."""

from integrations.senso import senso_client


# Policy category mapping for routing queries to the right context
POLICY_CATEGORIES = {
    "hr": {
        "keywords": [
            "salary", "compensation", "hire", "hiring", "termination", "pip",
            "performance", "benefits", "pto", "leave", "parental", "bonus",
            "equity", "stock", "onboarding", "offboarding", "interview",
            "promotion", "level", "band", "401k", "insurance", "health",
        ],
        "description": "HR & People policies — salary bands, benefits, hiring process, PIP, termination",
    },
    "it": {
        "keywords": [
            "laptop", "equipment", "provisioning", "software", "license",
            "access", "security", "mdm", "okta", "sso", "mfa", "device",
            "monitor", "vpn", "production", "github", "aws", "offboarding",
        ],
        "description": "IT provisioning — equipment, software, access levels, security requirements",
    },
    "finance": {
        "keywords": [
            "expense", "budget", "travel", "reimbursement", "approval",
            "purchase", "vendor", "card", "corporate", "hotel", "flight",
            "per diem", "receipt", "po", "purchase order", "spending",
        ],
        "description": "Finance — expense limits, travel policy, approvals, budget rules",
    },
    "compliance": {
        "keywords": [
            "i-9", "i9", "background check", "nda", "ip", "intellectual property",
            "e-verify", "everify", "compliance", "regulation", "california",
            "new york", "texas", "washington", "fcra", "ccpa", "harassment",
            "state-specific", "onboarding checklist",
        ],
        "description": "Compliance — I-9, background checks, NDA, IP assignment, state requirements",
    },
}


def detect_policy_category(query: str) -> list[str]:
    """Detect which policy categories a query relates to."""
    query_lower = query.lower()
    matches = []
    for category, info in POLICY_CATEGORIES.items():
        if any(kw in query_lower for kw in info["keywords"]):
            matches.append(category)
    return matches or ["hr", "compliance"]  # Default to HR + compliance


async def search_policies(query: str, top_k: int = 5) -> dict:
    """Search Senso policies with category context.

    Returns:
        {
            "query": str,
            "categories": list[str],
            "results": list[dict],
            "context_summary": str,
        }
    """
    categories = detect_policy_category(query)

    # Enrich query with category context
    category_hints = ", ".join(
        POLICY_CATEGORIES[c]["description"] for c in categories
    )
    enriched_query = f"{query} (context: {category_hints})"

    try:
        raw_results = await senso_client.search_policy(enriched_query, top_k=top_k)
    except Exception as e:
        return {
            "query": query,
            "categories": categories,
            "results": [],
            "context_summary": f"Policy search unavailable: {e}",
            "error": str(e),
        }

    # Extract results from Senso response
    results = raw_results.get("results", raw_results.get("data", []))
    if isinstance(raw_results, list):
        results = raw_results

    # Build context summary
    if results:
        snippets = []
        for r in results[:3]:
            text = r.get("text", r.get("content", r.get("snippet", str(r))))
            snippets.append(text[:200])
        context_summary = " | ".join(snippets)
    else:
        context_summary = f"No policy results found for: {query}. Categories searched: {', '.join(categories)}"

    return {
        "query": query,
        "categories": categories,
        "results": results,
        "context_summary": context_summary,
    }


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
