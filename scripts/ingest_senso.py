#!/usr/bin/env python3
"""Ingest policy documents into Senso via API.

Usage:
    python scripts/ingest_senso.py
    # or with custom API key:
    SENSO_API_KEY=tgr_xxx python scripts/ingest_senso.py
"""

import asyncio
import os
import sys
from pathlib import Path

import httpx

SENSO_BASE_URL = "https://apiv2.senso.ai/api/v1"
SENSO_API_KEY = os.getenv(
    "SENSO_API_KEY",
    "tgr_3XRknmB6MZM8ZfXUFg49dCQo1qQUSiAcsSIobdG3N0c",
)

POLICIES_DIR = Path(__file__).parent / "policies"

POLICY_FILES = [
    ("hr-policy.md", "text/markdown"),
    ("it-provisioning.md", "text/markdown"),
    ("finance-policy.md", "text/markdown"),
    ("compliance-checklist.md", "text/markdown"),
]


async def ingest_document(
    client: httpx.AsyncClient,
    filename: str,
    content: str,
    content_type: str,
) -> dict:
    """Upload a single document to Senso API."""
    headers = {
        "X-API-Key": SENSO_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "filename": filename,
        "content": content,
        "content_type": content_type,
    }

    resp = await client.post(
        f"{SENSO_BASE_URL}/documents",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


async def main():
    """Ingest all policy documents into Senso."""
    if not POLICIES_DIR.exists():
        print(f"ERROR: Policies directory not found: {POLICIES_DIR}")
        sys.exit(1)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for filename, content_type in POLICY_FILES:
            filepath = POLICIES_DIR / filename
            if not filepath.exists():
                print(f"  SKIP: {filename} not found")
                continue

            content = filepath.read_text()
            print(f"  Uploading {filename} ({len(content)} chars)...")

            try:
                result = await ingest_document(client, filename, content, content_type)
                doc_id = result.get("id", result.get("document_id", "unknown"))
                print(f"  OK: {filename} → doc_id={doc_id}")
            except httpx.HTTPStatusError as e:
                print(f"  WARN: {filename} → HTTP {e.response.status_code}: {e.response.text[:200]}")
            except Exception as e:
                print(f"  WARN: {filename} → {e}")

    print("\nIngestion complete.")


if __name__ == "__main__":
    asyncio.run(main())
