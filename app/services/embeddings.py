from app.clients.openrouter import OpenRouterClient


class EmbeddingsService:
    def __init__(self, openrouter_client: OpenRouterClient) -> None:
        self.openrouter_client = openrouter_client

    async def embed_text(self, text: str) -> list[float]:
        return await self.openrouter_client.create_embedding(text)
