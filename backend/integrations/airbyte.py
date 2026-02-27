"""Airbyte Agent Engine client — universal connector to customer systems."""

import httpx
from app.config import settings


class AirbyteClient:
    def __init__(self):
        self.base_url = settings.airbyte_base_url
        self.client_id = settings.airbyte_client_id
        self.client_secret = settings.airbyte_client_secret
        self.client = httpx.AsyncClient(timeout=60.0)
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        if not self.client_id or not self.client_secret:
            return ""
        resp = await self.client.post(f"{self.base_url}/v1/applications/token",
                                       json={"client_id": self.client_id,
                                             "client_secret": self.client_secret})
        resp.raise_for_status()
        data = resp.json()
        self._token = data.get("access_token", data.get("token", ""))
        return self._token

    async def _auth_headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def list_connections(self) -> dict:
        headers = await self._auth_headers()
        resp = await self.client.get(f"{self.base_url}/v1/connections", headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def trigger_sync(self, connection_id: str) -> dict:
        headers = await self._auth_headers()
        resp = await self.client.post(f"{self.base_url}/v1/jobs", headers=headers,
                                       json={"connection_id": connection_id, "job_type": "sync"})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


airbyte_client = AirbyteClient()
