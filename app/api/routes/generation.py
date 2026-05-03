import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.generation import GenerationService
from app.services.storage import repository_bundle
from app.services.text_generation import create_text_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generation", tags=["generation"])


@router.post("", response_model=GenerationResponse)
async def generate_post(
    payload: GenerationRequest,
) -> GenerationResponse:
    logger.info("API generation request received", extra={"topic": payload.topic})
    settings = get_settings()
    async with repository_bundle() as repositories:
        service = GenerationService(
            generation_logs_repository=repositories.generation_logs,
            text_generator=create_text_generator(settings),
        )
        result = await service.generate_post(
            topic=payload.topic,
            custom_topic=payload.custom_topic,
            user_request=payload.user_request,
        )
        await repositories.commit()
    return GenerationResponse(status=result.status, generated_text=result.generated_text)
