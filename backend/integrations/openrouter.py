"""OpenRouter LLM client — Claude Sonnet via OpenRouter."""

import json
import httpx
from app.config import settings


class OpenRouterClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def api_key(self):
        return settings.openrouter_api_key

    @property
    def model(self):
        return settings.openrouter_model

    @property
    def base_url(self):
        return settings.openrouter_base_url

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   temperature: float = 0.3, max_tokens: int = 4096) -> dict:
        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        for attempt in range(3):
            resp = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json",
                         "HTTP-Referer": "https://backoffice.ai",
                         "X-Title": "backoffice.ai"},
                json=payload)
            resp.raise_for_status()
            text = resp.text
            if text and text.strip():
                import json as _json
                return _json.loads(text)
            if attempt < 2:
                import asyncio
                await asyncio.sleep(1)
        # Last resort: return a synthetic response
        return {"choices": [{"message": {"content": "I received an empty response from the AI model. Please try again."}}]}

    async def structured_output(self, prompt: str, system: str = "") -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages,
                   "temperature": 0.2, "max_tokens": 4096,
                   "response_format": {"type": "json_object"}}
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://backoffice.ai",
                     "X-Title": "backoffice.ai"},
            json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}

    async def close(self):
        await self.client.aclose()


openrouter_client = OpenRouterClient()
