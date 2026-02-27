"""Yutori API client — web automation for portals with no API."""

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
        resp = await self.client.get(f"{self.base_url}/browsing/tasks/{task_id}",
                                      headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    async def wait_for_task(self, task_id: str, max_polls: int = 30, interval: float = 2.0) -> dict:
        for _ in range(max_polls):
            result = await self.get_task_status(task_id)
            if result.get("status") in ("completed", "failed", "error"):
                return result
            await asyncio.sleep(interval)
        return {"status": "timeout", "task_id": task_id}

    async def close(self):
        await self.client.aclose()


yutori_client = YutoriClient()
