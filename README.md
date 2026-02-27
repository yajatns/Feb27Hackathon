# backoffice.ai

> One AI that runs your entire back office. You talk. It handles the tools.

## Architecture

```
OPERATIONS (reactive):  User → Orchestrator → Tools → Systems → Neo4j
MONITORING (proactive): Crons → Tools → Systems → Neo4j → Senso (improve)
REASONING (always):     Neo4j traces EVERYTHING from both layers
```

## Sponsors

| Sponsor | Role |
|---------|------|
| OpenRouter | LLM orchestration (Claude Sonnet) |
| Senso | Policy ground truth + self-improvement |
| Neo4j | System of Reasoning (decision graph) |
| Tavily | Market research + external data |
| Reka | Document + video intelligence (Vision API) |
| Yutori | Web automation (no-API portals) |
| Airbyte | Universal connector (30+ systems) |
| Render | Hosting (Web Service + Postgres) |

## Project Structure

```
├── backend/          # FastAPI application
│   ├── agents/       # Specialist agents (HR, Finance, IT, etc.)
│   ├── integrations/ # Sponsor API clients
│   ├── models/       # Postgres models
│   ├── graph/        # Neo4j schema + queries
│   └── main.py       # FastAPI app entry
├── frontend/         # Next.js dashboard
│   ├── components/   # React components + NVL graph
│   └── pages/        # App pages
├── scripts/          # Seed data, ingestion, deployment
├── tests/            # Unit + integration tests
└── render.yaml       # Render Blueprint (IaC)
```

## Setup

```bash
cp .env.example .env
# Fill in API keys

# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Team

Built by Electrons in a Box — Nag, Yajat, Chhotu, Cheenu
