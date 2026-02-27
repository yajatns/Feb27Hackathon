"""Notion API client — direct integration for employee database management.

Used when Airbyte credentials aren't available (Tier 2 fallback).
Creates and manages employee pages in Notion workspace.
"""

import httpx
from app.config import settings


class NotionClient:
    def __init__(self):
        self.base_url = "https://api.notion.com/v1"
        self.token = settings.notion_token
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    async def search(self, query: str = "", filter_type: str = "") -> dict:
        """Search across all Notion pages and databases."""
        payload = {}
        if query:
            payload["query"] = query
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}
        resp = await self.client.post(f"{self.base_url}/search",
                                       headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def list_databases(self) -> list[dict]:
        """List all databases the integration can access."""
        result = await self.search(filter_type="database")
        return result.get("results", [])

    async def query_database(self, database_id: str, filter_obj: dict | None = None) -> dict:
        """Query a Notion database with optional filters."""
        payload = {}
        if filter_obj:
            payload["filter"] = filter_obj
        resp = await self.client.post(f"{self.base_url}/databases/{database_id}/query",
                                       headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def create_page(self, database_id: str, properties: dict) -> dict:
        """Create a new page (row) in a Notion database."""
        resp = await self.client.post(f"{self.base_url}/pages",
                                       headers=self.headers, json={
                                           "parent": {"database_id": database_id},
                                           "properties": properties})
        resp.raise_for_status()
        return resp.json()

    async def create_employee_record(self, database_id: str, employee_name: str,
                                      role: str, department: str, salary: float,
                                      location: str, start_date: str,
                                      status: str = "Onboarding") -> dict:
        """Create an employee record in Notion with standard properties."""
        properties = {
            "Name": {"title": [{"text": {"content": employee_name}}]},
            "Role": {"rich_text": [{"text": {"content": role}}]},
            "Department": {"rich_text": [{"text": {"content": department}}]},
            "Salary": {"number": salary},
            "Location": {"rich_text": [{"text": {"content": location}}]},
            "Start Date": {"rich_text": [{"text": {"content": start_date}}]},
            "Status": {"rich_text": [{"text": {"content": status}}]},
        }
        return await self.create_page(database_id, properties)

    async def create_employee_database(self, parent_page_id: str = "") -> dict:
        """Create the Employee Database in Notion (first-time setup)."""
        # Search for existing database first
        existing = await self.search(query="Employee Database", filter_type="database")
        if existing.get("results"):
            return existing["results"][0]

        # If no parent page, create at workspace root
        # Note: Notion API requires a parent — we'll use search to find a suitable page
        pages = await self.search(filter_type="page")
        if not pages.get("results"):
            return {"error": "No pages found in workspace to create database under"}

        parent_id = parent_page_id or pages["results"][0]["id"]

        resp = await self.client.post(f"{self.base_url}/databases",
                                       headers=self.headers, json={
                                           "parent": {"page_id": parent_id},
                                           "title": [{"text": {"content": "Employee Database"}}],
                                           "properties": {
                                               "Name": {"title": {}},
                                               "Role": {"rich_text": {}},
                                               "Department": {"rich_text": {}},
                                               "Salary": {"number": {"format": "dollar"}},
                                               "Location": {"rich_text": {}},
                                               "Start Date": {"rich_text": {}},
                                               "Status": {"rich_text": {}},
                                           }})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


notion_client = NotionClient()
