from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GenerationLog


class GenerationLogsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
        model_name: str | None = None,
        retrieved_post_ids: list[int] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> GenerationLog:
        log = GenerationLog(
            topic=topic,
            custom_topic=custom_topic,
            user_request=user_request,
            prompt=prompt,
            generated_text=generated_text,
            status=status,
            model_name=model_name,
            retrieved_post_ids=retrieved_post_ids,
            metadata_=metadata,
        )
        self.session.add(log)
        await self.session.flush()
        return log
