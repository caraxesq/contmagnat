import httpx
import logging

from app.core.config import Settings
from app.core.errors import GenerationNotConfiguredError

logger = logging.getLogger(__name__)


class OpenRouterClient:
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def create_embedding(self, text: str) -> list[float]:
        if not self.settings.openrouter_api_key or not self.settings.openrouter_embedding_model:
            raise GenerationNotConfiguredError("OpenRouter embeddings are not configured")

        payload = {
            "model": self.settings.openrouter_embedding_model,
            "input": text,
        }
        data = await self._post("/embeddings", payload)
        return list(data["data"][0]["embedding"])

    async def create_chat_completion(self, prompt: str) -> str:
        if not self.settings.openrouter_api_key or not self.settings.openrouter_chat_model:
            raise GenerationNotConfiguredError("OpenRouter chat completions are not configured")

        payload = {
            "model": self.settings.openrouter_chat_model,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = await self._post("/chat/completions", payload)
        content = str(data["choices"][0]["message"]["content"])
        logger.info("OpenRouter chat completion received: %s", content)
        return content

    async def _post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            try:
                response = await client.post(path, json=payload, headers=headers)
                response.raise_for_status()
                return dict(response.json())
            except httpx.HTTPError:
                logger.exception("OpenRouter request failed: %s", path)
                raise
