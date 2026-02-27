# T3: Senso Policy Ingestion + Reka Vision Document Analysis

## Branch
`chhotu/T3-senso-reka` off latest main

## Context
backoffice.ai hackathon. Senso = self-improving policy engine. Reka = Vision API for document analysis.

## Requirements

### 1. Senso Policy Documents (`scripts/ingest_senso.py`)
Write and ingest these policy docs via Senso API (`POST https://apiv2.senso.ai/api/v1/documents`):
- **hr-policy.md** — hiring process, salary bands by role/level/location, PIP policy, termination, benefits eligibility
- **it-provisioning.md** — equipment provisioning (laptop, monitors, software licenses), access levels by role, security requirements
- **finance-policy.md** — expense limits, approval thresholds, travel policy, reimbursement, budget owner rules
- **compliance-checklist.md** — I-9 verification, background check, NDA, IP assignment, state-specific requirements (CA, NY, TX, WA)

Each doc should be realistic and detailed enough for the AI to query meaningfully.

API: `POST /api/v1/documents` with `X-API-Key: tgr_3XRknmB6MZM8ZfXUFg49dCQo1qQUSiAcsSIobdG3N0c`

Also create a search helper: `backend/integrations/senso_policies.py` that wraps policy search with context.

### 2. Reka Vision Document Processor (`backend/integrations/reka_vision.py`)
Use Reka's **Vision API** (NOT chat multimodal) to analyze uploaded documents:
- Endpoint: `POST https://vision-agent.api.reka.ai/v1/vision/analyze` (verify actual endpoint)
- Header: `X-Api-Key: e91479eb0c682d254792bdea6f560afd360dc89c28a3d502e5c89eb094582e9a`
- Accept image/PDF uploads, extract structured data
- Use cases: analyze offer letters, ID documents, tax forms, compliance certificates

Create route: `POST /api/analyze-document` that accepts file upload → Reka Vision → structured extraction → Neo4j logging

### 3. Policy Query Route Enhancement (`backend/routes/query.py`)
Update the /query endpoint to route policy questions to Senso first, then augment with LLM reasoning.

### 4. Tests
- Test Senso ingestion script
- Test Reka Vision client
- Test document analysis route

## After completion
git add, commit, push, create PR against main.

When completely finished, run: openclaw system event --text "Done: T3 Senso policy ingestion + Reka Vision document analysis" --mode now
