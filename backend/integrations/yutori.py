"""Yutori API client — web automation for portals with no API.

Used by IT Agent for benefits enrollment, insurance forms, government filings.
Supports structured output schemas for extracting data from web pages.
"""

import asyncio
import httpx
from app.config import settings


class YutoriClient:
    def __init__(self):
        self.base_url = settings.yutori_base_url
        self.api_key = settings.yutori_api_key
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def headers(self) -> dict:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def create_task(self, task: str, start_url: str = "",
                          output_schema: dict | None = None) -> dict:
        """Create a browsing automation task."""
        payload = {"task": task}
        if start_url:
            payload["start_url"] = start_url
        if output_schema:
            payload["output_schema"] = output_schema
        resp = await self.client.post(f"{self.base_url}/browsing/tasks",
                                       headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_task_status(self, task_id: str) -> dict:
        """Check the status of a browsing task."""
        resp = await self.client.get(f"{self.base_url}/browsing/tasks/{task_id}",
                                      headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    async def wait_for_task(self, task_id: str, max_polls: int = 30, interval: float = 2.0) -> dict:
        """Poll until a browsing task completes."""
        for _ in range(max_polls):
            result = await self.get_task_status(task_id)
            if result.get("status") in ("completed", "failed", "error"):
                return result
            await asyncio.sleep(interval)
        return {"status": "timeout", "task_id": task_id}

    async def enroll_benefits(self, employee_name: str, start_date: str,
                               portal_url: str = "") -> dict:
        """Specialized: enroll employee in benefits portal."""
        task = f"Navigate to benefits enrollment portal. Enroll {employee_name} " \
               f"starting {start_date}. Fill out required forms and submit."
        return await self.create_task(task=task, start_url=portal_url)

    async def fill_government_form(self, form_type: str, employee_data: dict,
                                    portal_url: str = "") -> dict:
        """Specialized: fill out government forms (I-9, W-4, etc.)."""
        data_str = ", ".join(f"{k}: {v}" for k, v in employee_data.items())
        task = f"Fill out {form_type} form with this employee data: {data_str}. " \
               f"Complete all required fields and submit."
        return await self.create_task(task=task, start_url=portal_url,
                                       output_schema={"type": "object", "properties": {
                                           "confirmation_number": {"type": "string"},
                                           "status": {"type": "string"},
                                           "submitted_at": {"type": "string"}}})

    async def scrape_insurance_rates(self, location: str, plan_type: str = "health") -> dict:
        """Specialized: scrape insurance rates from carrier portals."""
        task = f"Look up {plan_type} insurance rates for employees in {location}. " \
               f"Extract plan names, monthly premiums, and coverage details."
        return await self.create_task(task=task,
                                       output_schema={"type": "object", "properties": {
                                           "plans": {"type": "array", "items": {
                                               "type": "object", "properties": {
                                                   "name": {"type": "string"},
                                                   "monthly_premium": {"type": "number"},
                                                   "coverage": {"type": "string"}}}}}})

    async def close(self):
        await self.client.aclose()


yutori_client = YutoriClient()
