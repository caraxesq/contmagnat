from dataclasses import dataclass
from typing import Protocol

from app.services.prompt_builder import build_generation_prompt
from app.services.text_generation import MockTextGenerator, TextGenerator
from app.core.errors import GenerationNotConfiguredError

import logging

logger = logging.getLogger(__name__)


class GenerationLogsRepositoryProtocol(Protocol):
    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
        **kwargs: object,
    ) -> object:
        pass


@dataclass(frozen=True)
class GenerationResult:
    status: str
    generated_text: str


class GenerationService:
    def __init__(
        self,
        *,
        generation_logs_repository: GenerationLogsRepositoryProtocol | None = None,
        text_generator: TextGenerator | None = None,
    ) -> None:
        self.generation_logs_repository = generation_logs_repository
        self.text_generator = text_generator or MockTextGenerator()

    async def generate_post(
        self,
        *,
        topic: str,
        user_request: str,
        custom_topic: str | None = None,
        style_examples: list[str] | None = None,
    ) -> GenerationResult:
        prompt_topic = f"{topic}: {custom_topic}" if custom_topic else topic
        prompt = build_generation_prompt(
            topic=prompt_topic,
            user_request=user_request,
            style_examples=style_examples or [],
        )
        logger.info("Generation request received", extra={"topic": topic, "custom_topic": custom_topic})

        try:
            generated_text = await self.text_generator.generate(prompt)
            logger.info("Model response received: %s", generated_text)
            status = "ok"
        except GenerationNotConfiguredError as error:
            logger.warning("Generation provider is not configured: %s", error)
            generated_text = f"Ошибка генерации: {error}"
            status = "error"
        except Exception:
            logger.exception("Generation failed")
            generated_text = "Ошибка генерации. Подробности записаны в лог."
            status = "error"

        if self.generation_logs_repository is not None:
            await self.generation_logs_repository.add_log(
                topic=topic,
                custom_topic=custom_topic,
                user_request=user_request,
                generated_text=generated_text,
                status=status,
                prompt=prompt,
            )

        return GenerationResult(status=status, generated_text=generated_text)
