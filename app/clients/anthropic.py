import logging

import httpx

from app.core.config import Settings
from app.core.errors import GenerationNotConfiguredError

logger = logging.getLogger(__name__)


class AnthropicClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.anthropic_base_url.rstrip("/")
        self.messages_path = "/v1/messages"

    async def create_message(self, prompt: str) -> str:
        if not self.base_url or not self.api_token or not self.settings.anthropic_model:
            raise GenerationNotConfiguredError(
                "Anthropic generation requires base URL, token and model"
            )

        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = await self._post(self.messages_path, payload)
        blocks = data.get("content", [])
        if not isinstance(blocks, list):
            return ""
        return "\n".join(
            str(block.get("text", ""))
            for block in blocks
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()

    async def _post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        headers = self.headers()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            try:
                response = await client.post(path, json=payload, headers=headers)
                response.raise_for_status()
                return dict(response.json())
            except httpx.HTTPError:
                logger.exception("Anthropic request failed: %s", path)
                raise

    @property
    def api_token(self) -> str:
        return self.settings.anthropic_auth_token or self.settings.anthropic_api_key

    def headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_token,
            "Authorization": f"Bearer {self.api_token}",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
