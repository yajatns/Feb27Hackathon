# backoffice.ai — 3-Minute Demo Script

**Tagline:** "One AI that runs your entire back office. You talk. It handles the tools."

---

## Act 1: REACTIVE — "Hire someone" (60 seconds)

**[Open dashboard → Hire page]**

> "Meet backoffice.ai. One AI orchestrator that manages your entire back office."

> "Let's say HR needs to hire a senior engineer. Instead of juggling 5 different tools, you just tell the AI what you need."

**[Fill hire form: "Sarah Chen", Senior Engineer, Engineering, $180,000, San Francisco]**
**[Click Submit → Watch agent pipeline animate]**

> "Watch what happens. The orchestrator breaks this into specialist tasks and delegates to AI agents — each an expert in their domain."

> "Maya researches salary benchmarks via Tavily deep search. Sam checks our internal policies through Senso — our self-improving policy engine. Compliance verifies everything meets regulatory requirements. Alex provisions accounts and onboards."

**[Point to pipeline: Maya ✅ → Sam ✅ → Compliance ✅ → Alex ✅]**

> "Four agents. Four tools. One conversation. The hire is processed end-to-end."

---

## Act 2: PROACTIVE — "It watches while you sleep" (60 seconds)

**[Switch to dashboard home → Show monitoring crons]**

> "But backoffice.ai doesn't just respond — it proactively monitors your business."

> "Three monitoring crons run continuously:"

> "**Salary compliance** scans all employees against market data via Tavily. If someone's 20% below benchmark, it flags it before they quit."

> "**Self-improvement** — this is key. Every human override creates a LEARNED edge in our Neo4j knowledge graph. After 3+ overrides in the same direction, the AI automatically updates its policies through Senso. It literally learns from your corrections."

> "**Video audit** uses Reka Vision to analyze training videos and compliance footage. No human review needed."

**[Show /api/crons/types response with 3 cron types]**

---

## Act 3: INTELLIGENCE — "The knowledge graph" (60 seconds)

**[Switch to Graph page → Show Neo4j visualization]**

> "Every decision, every delegation, every lesson is traced in our Neo4j System of Reasoning."

**[Point to colored edges]**

> "Blue edges are DELEGATED — who assigned what. Green edges are COMPLETED — what got done. And gold edges — those are LEARNED. That's the AI improving itself."

> "When a manager overrides a salary decision..."

**[Show override concept]**

> "...it creates a LEARNED edge. After enough overrides, the policy automatically updates via Senso. The AI evolves its own ground truth."

**[Show Airbyte integration]**

> "And through Airbyte's 600+ connectors, this orchestrator plugs into ANY system your business already uses — Notion, Salesforce, Stripe, Jira. No new tools to learn. It speaks their language."

---

## Closing (15 seconds)

> "backoffice.ai. One AI orchestrator. Real integrations — Senso, Reka, Tavily, Yutori, Airbyte, OpenRouter, Render, Notion. Zero mocks. A self-improving system that gets smarter with every human decision."

> "Your back office, on autopilot."

---

## URLs for Demo

- **Dashboard:** https://feb27hackathon.onrender.com (or https://backoffice-dashboard-kqya.onrender.com)
- **API:** https://backoffice-api-ep7k.onrender.com
- **Swagger:** https://backoffice-api-ep7k.onrender.com/docs
- **GitHub:** https://github.com/yajatns/Feb27Hackathon

## Sponsor Integration Callouts

| Sponsor | How We Use It | Demo Moment |
|---------|--------------|-------------|
| **Senso** | Self-improving policy engine — agents query before decisions, overrides feed back | Act 2: LEARNED edges → policy updates |
| **Reka** | Vision API for document/video analysis | Act 2: Video audit cron |
| **Tavily** | Deep research — salary benchmarks, regulatory checks | Act 1: Maya's research |
| **Yutori** | Portal automation for systems without APIs | Act 1: Alex's provisioning |
| **Airbyte** | 600+ connectors — universal integration layer | Act 3: "Plugs into ANY system" |
| **OpenRouter** | LLM orchestration — Claude Sonnet function calling | Core: Powers the orchestrator |
| **Render** | 3 services deployed (API + Frontend + Postgres) | "Live demo, deployed on Render" |
| **Notion** | Employee database sync via Airbyte agent | Act 1: Data sync after hire |

## Backup Plans

- **If Render is slow:** Use Swagger UI directly (`/docs`) — still impressive
- **If Neo4j is down:** Frontend has built-in demo graph data
- **If API keys fail:** Show the pipeline flow (agents still execute, just with fallback responses)
- **If frontend doesn't load:** Demo via curl commands + Swagger — shows the real API
