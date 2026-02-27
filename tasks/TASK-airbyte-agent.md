# Enhanced Airbyte Specialist Agent with Agent Connectors

## Branch
`chhotu/airbyte-agent` off latest main

## Context
Use airbyte-agent-connectors (https://github.com/airbytehq/airbyte-agent-connectors) — standalone Python SDKs that give AI agents typed access to SaaS APIs. No hosted Airbyte instance needed.

## Requirements

### 1. Install agent connectors
Add to requirements.txt:
- airbyte-agent-github
- airbyte-agent-notion  (if available, otherwise use our existing notion.py)

### 2. Enhanced Airbyte Agent (`backend/agents/airbyte_agent.py`)
Replace/enhance the existing basic airbyte.py integration. The new agent should:
- Be a specialist agent (extends BaseAgent)
- Discover available connectors programmatically
- Configure connectors from natural language instructions
- Read data from any connected source
- Format and return structured results for the orchestrator
- Log all operations to Neo4j

Key methods:
- `list_connectors()` — what systems can we connect to?
- `connect_source(source_type, config)` — set up a new connection
- `read_data(source, streams)` — fetch data from a source
- `sync_to_notion(data, database_id)` — write results to Notion

### 3. Orchestrator Integration
Update the hire route so when the orchestrator needs external data (e.g., "pull candidate info from GitHub", "sync hire to Notion"), it delegates to the Airbyte agent.

### 4. Demo Route (`backend/routes/connectors.py`)
- GET /api/connectors — list available Airbyte connectors
- POST /api/connectors/read — read from a connector
- POST /api/connectors/sync — sync data between systems

### 5. Tests
- Test connector discovery
- Test data reading (mock the actual API calls)
- Test route handlers

## After completion
git add, commit, push, create PR against main.

When completely finished, run: openclaw system event --text "Done: Enhanced Airbyte agent with agent connectors" --mode now
