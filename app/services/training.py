from dataclasses import dataclass

from app.services.rag import RagIndexService


@dataclass(frozen=True)
class TrainingResult:
    status: str
    message: str


class TrainingService:
    def __init__(self, rag_index_service: RagIndexService | None = None) -> None:
        self.rag_index_service = rag_index_service

    async def save_and_train(
        self,
        *,
        topic: str | None = None,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> TrainingResult:
        if self.rag_index_service is None:
            return TrainingResult(
                status="skipped",
                message="Данные сохранены. RAG-индекс не настроен.",
            )
        if topic:
            result = await self.rag_index_service.rebuild_collection(
                topic=topic,
                custom_topic=custom_topic,
                style_scope=style_scope,
            )
        else:
            result = await self.rag_index_service.rebuild_all()
        return TrainingResult(
            status="ok",
            message=f"RAG-индекс обновлен. Постов в индексе: {result.indexed_count}.",
        )
