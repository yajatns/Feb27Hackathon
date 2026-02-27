# Deep Codebase Review — backoffice.ai

## Branch
`chhotu/deep-review` off latest main

## Objective
Comprehensive audit of the entire codebase. Find and fix ALL issues before demo.

## Review Checklist

### 1. Import Consistency
- All imports should be relative to `backend/` dir
- Check for circular imports
- Check for missing imports that would crash at runtime

### 2. Missing Definitions
- Find any class/function referenced but not defined (like UserOverrideResponse was)
- Check all Pydantic models match what routes expect
- Check all route handlers exist and are properly registered

### 3. Error Handling
- All integration clients should handle missing API keys gracefully
- No unhandled exceptions that crash the server
- Proper try/except around external API calls

### 4. Environment Variables
- All env vars in config.py should have safe defaults
- App should start even with zero env vars set
- Check .env.example matches config.py

### 5. Route Registration
- Every route in routes/ is registered in main.py
- No duplicate route paths
- All response models defined

### 6. Test Coverage Gaps
- Run: cd backend && PYTHONPATH=. python3 -m pytest ../tests/ -v 2>&1
- Fix any failing tests
- Add tests for uncovered critical paths

### 7. Neo4j Integration
- graph/client.py and integrations/neo4j_client.py — are these redundant?
- Ensure graceful fallback when Neo4j is unavailable

### 8. Frontend-Backend Contract
- Check frontend API calls in lib/api.ts match backend routes
- Check response shapes match what frontend expects

### 9. Database Models
- SQLAlchemy models match Pydantic schemas
- All foreign keys valid
- Migration-ready

### 10. Security
- No hardcoded API keys
- CORS configured appropriately
- Input validation on all endpoints

## Output
Create `REVIEW.md` in repo root with:
- Issues found (severity: CRITICAL/HIGH/MEDIUM/LOW)
- Fixes applied
- Remaining concerns

Fix everything you can. Commit fixes, push, create PR.

When completely finished, output "REVIEW COMPLETE" as your final message.
