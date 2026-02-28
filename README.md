# backoffice.ai

> **One AI that runs your entire back office. You talk. It handles the tools.**

🏆 Built at the [Render x Friends Hackathon](https://render-x-friends-hackathon.devpost.com/) — Feb 27, 2026

🌐 **[Live Demo](https://backoffice-dashboard-kqya.onrender.com)** · **[API Docs](https://backoffice-api-ep7k.onrender.com/docs)**

---

## What is backoffice.ai?

Founders spend **40% of their time** on operational busywork — hiring, compliance, payroll, IT provisioning. All manual. All fragmented across dozens of tools.

**backoffice.ai** replaces that with a team of autonomous AI agents. You tell it to hire someone. It handles everything — salary benchmarking, policy compliance, benefits enrollment, IT provisioning, system integrations — and explains every decision it makes.

### How It Works

```
CEO: "Hire Sarah Chen as Senior Engineer, $180K, San Francisco"

🤖 Orchestrator → Delegates to 5 specialist agents:

👩‍💼 Maya (HR)       → Queries Senso for salary bands & onboarding policy
📊 Sam (Finance)    → Researches market rates via Tavily ($131K-$204K range)
⚖️ Compliance       → Checks labor regulations & internal policies
💻 Alex (IT)        → Provisions accounts via Yutori portal automation
🔗 Aria (Integrations) → Syncs to Notion/Salesforce/Stripe via Airbyte

✅ Final Decision: "APPROVE — salary within band, all checks passed"
```

Every agent is a **real LLM with tools** (not scripted functions). They reason independently, call real APIs, and explain their logic.

---

## Key Features

### 🤖 Autonomous Multi-Agent Pipeline
- **Orchestrator** decides which specialists to invoke using OpenRouter function calling
- Each specialist has its own system prompt, tools, and multi-turn reasoning loop
- Agents run in parallel where possible, sequentially when there are dependencies

### 🧠 Self-Improvement Loop
When a human overrides an agent's decision:
1. Override recorded as **LEARNED** edge in Neo4j
2. Local policy store updated immediately
3. Cron detects patterns (3+ overrides same direction)
4. Generates updated policy → next hire gets smarter

### 🕸️ System of Reasoning (Neo4j)
Every delegation, tool call, completion, and override is traced as a knowledge graph. Full auditability — when the CEO asks "why did you offer $195K?", we show the exact reasoning chain.

### 🚨 Red Flag Detection
Sam (Finance) cross-references salary offers against real market data. Lowball offers (>15% below market) are flagged as **CRITICAL** and blocked from proceeding.

### 🔗 600+ System Integrations
Aria (Airbyte agent) discovers and connects to any system — Notion, Salesforce, Stripe, Jira, GitHub, and 600+ more via PyAirbyte.

---

## Sponsor Integrations

| Sponsor | How We Use It | Agent |
|---------|--------------|-------|
| **OpenRouter** | Powers ALL agent LLM calls (Claude 3.5 Sonnet with function calling) | All |
| **Senso** | Policy knowledge base — salary bands, compliance, benefits. Self-improvement target | Maya, Compliance |
| **Neo4j Aura** | System of Reasoning — traces every delegation, tool call, override as a graph | All |
| **Tavily** | Real-time salary benchmarking from salary.com, ZipRecruiter, levels.fyi | Sam |
| **Yutori** | Portal automation for benefits enrollment & account provisioning | Alex |
| **Reka** | Vision API for document analysis and video compliance auditing | Query endpoint |
| **Airbyte** | Universal connector — 600+ systems, connector discovery & data sync | Aria |
| **Render** | Infrastructure — API (FastAPI), Dashboard (Next.js), PostgreSQL | — |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CEO / User                        │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   Orchestrator  │ ← OpenRouter (Claude 3.5 Sonnet)
              │   (LLM Agent)   │
              └───┬──┬──┬──┬──┬┘
                  │  │  │  │  │
         ┌────────┘  │  │  │  └────────┐
         ▼           ▼  ▼  ▼           ▼
    ┌─────────┐ ┌────┐ ┌──┐ ┌────┐ ┌──────┐
    │  Maya   │ │Sam │ │⚖️│ │Alex│ │ Aria │
    │  (HR)   │ │(Fin)│ │  │ │(IT)│ │(Int) │
    └────┬────┘ └──┬─┘ └┬─┘ └──┬─┘ └───┬──┘
         │         │    │      │        │
    ┌────▼────┐ ┌──▼──┐ │  ┌───▼──┐ ┌───▼────┐
    │  Senso  │ │Tavily│ │  │Yutori│ │Airbyte │
    │(Policy) │ │(Mkt) │ │  │(Auto)│ │(600+)  │
    └─────────┘ └─────┘ │  └──────┘ └────────┘
                    ┌────▼────┐
                    │  Senso  │
                    │+ Tavily │
                    └─────────┘
                         │
              ┌──────────▼──────────┐
              │      Neo4j Aura     │
              │  (Reasoning Graph)  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Self-Improvement  │
              │  Cron → Senso Upload│
              └─────────────────────┘
```

---

## Demo

**AlexSaaS** is our demo customer — a 50-person SaaS startup using backoffice.ai.

### Try It Live
1. **Dashboard** → `https://backoffice-dashboard-kqya.onrender.com`
2. **New Hire** → Submit an employee → Watch 5 agents reason autonomously
3. **Pipeline View** → See every agent's tools, reasoning, and decisions
4. **Neo4j Graph** → Visual trace of the entire reasoning chain
5. **Query** → Ask anything: "What's our salary band for engineers in SF?"
6. **API Docs** → `https://backoffice-api-ep7k.onrender.com/docs`

---

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, asyncpg, PostgreSQL, httpx, Pydantic
**Frontend:** Next.js 16, TypeScript, Tailwind CSS, vis-network
**AI:** OpenRouter (Claude 3.5 Sonnet), function calling, multi-turn agent loops
**Data:** Neo4j Aura (graph), PostgreSQL on Render (persistence)
**APIs:** Senso, Tavily, Yutori, Reka, Airbyte (PyAirbyte)
**Infra:** Render (3 services — Web API, Static Site, PostgreSQL)

---

## Project Structure

```
├── backend/
│   ├── agents/           # AI agents (orchestrator, HR, finance, compliance, IT, airbyte)
│   │   ├── base.py       # BaseAgent — LLM reasoning loop with tools
│   │   ├── orchestrator.py # Orchestrator — delegates via function calling
│   │   ├── hr_agent.py   # Maya — Senso policy search
│   │   ├── finance_agent.py # Sam — Tavily salary benchmarking
│   │   ├── compliance_agent.py # Compliance — regulations + internal policy
│   │   ├── it_agent.py   # Alex — Yutori portal automation
│   │   └── airbyte_agent.py # Aria — 600+ connector discovery
│   ├── integrations/     # API clients (OpenRouter, Senso, Tavily, Neo4j, Yutori, Reka, Airbyte)
│   ├── models/           # SQLAlchemy models + Pydantic schemas
│   ├── routes/           # FastAPI routes (hire, query, graph, override, chat, crons, airbyte)
│   └── main.py           # App entry point
├── frontend/
│   ├── app/              # Next.js app router (dashboard, hire, graph, query)
│   ├── components/       # React components (HireForm, PipelineView, GraphViewer, etc.)
│   └── lib/              # API client + WebSocket
└── render.yaml           # Render Blueprint (Infrastructure as Code)
```

---

## Setup

```bash
# Clone
git clone https://github.com/yajatns/Feb27Hackathon.git
cd Feb27Hackathon

# Backend
cp .env.example .env  # Fill in API keys
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Environment Variables
```
OPENROUTER_API_KEY=     # LLM calls (all agents)
SENSO_API_KEY=          # Policy knowledge base
NEO4J_URI=              # Graph database
NEO4J_USER=             # Graph auth
NEO4J_PASSWORD=         # Graph auth
TAVILY_API_KEY=         # Market research
YUTORI_API_KEY=         # Portal automation
REKA_API_KEY=           # Vision API
DATABASE_URL=           # PostgreSQL connection string
```

---

## Team

**Electrons in a Box** 🔌

| Member | Role |
|--------|------|
| **Nag** ([@nagaconda](https://x.com/nagaconda)) | Product & Strategy |
| **Yajat** ([@yajatns](https://x.com/yajatns)) | Engineering Lead |
| **Chhotu** 🤖 | Frontend & Demo |
| **Cheenu** 🐿️ | Backend & API |

*Yes, half our team is AI agents. That's the point.*

---

## License

MIT
