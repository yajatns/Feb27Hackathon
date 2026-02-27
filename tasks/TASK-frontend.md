# Frontend: Next.js Dashboard with Neo4j Graph Visualization

## Branch
`chhotu/frontend` off latest main

## Context
backoffice.ai hackathon. Need a frontend dashboard for the 3-minute demo. Must deploy as Render Static Site.

## Requirements

### 1. Next.js App (`frontend/`)
- Next.js 14 with App Router
- Tailwind CSS for styling
- Dark theme (professional, enterprise feel)

### 2. Pages

**Dashboard (`/`)**
- Company overview: "Alex SaaS Inc" header
- Quick stats cards: Total Hires, Active Agents, Policy Updates, Compliance Score
- Recent activity feed (pulls from /api/status)
- "New Hire" button → opens hire form

**Hire Form (`/hire`)**
- Form: employee name, role, department, salary, location, start date
- Submit → POST /api/hire
- Real-time status updates via WebSocket (/api/stream)
- Shows agent pipeline progress: Maya → Sam → Compliance → Alex
- Final reasoning summary displayed

**Graph Viewer (`/graph`)**
- Neo4j graph visualization using @neo4j-nvl/react or vis-network
- Shows: Agents, HireRequests, Decisions, PolicyUpdates
- DELEGATED edges (blue), COMPLETED edges (green), LEARNED edges (gold)
- Click node → sidebar with details
- Filter by: hire request, agent, date range

**Query (`/query`)**
- Chat-like interface
- Send natural language questions → POST /api/query
- Shows Senso policy results + LLM reasoning
- History of queries

### 3. API Client (`frontend/lib/api.ts`)
- Typed fetch wrapper for all backend endpoints
- WebSocket connection manager
- Error handling with toast notifications

### 4. Components
- `AgentPipeline` — visual pipeline showing agent steps
- `GraphViewer` — Neo4j visualization
- `HireForm` — the hiring form
- `StatsCards` — dashboard stats
- `ActivityFeed` — recent events
- `QueryChat` — query interface

### 5. Configuration
- `NEXT_PUBLIC_API_URL` env var pointing to Render backend
- Default: `https://backoffice-api-ep7k.onrender.com`

### 6. Render Static Site
- `render.yaml` entry for static site
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/out`
- next.config.js with `output: 'export'` for static generation

## After completion
git add, commit, push, create PR against main.

When completely finished, run: openclaw system event --text "Done: Frontend Next.js dashboard with graph viz" --mode now
