import logging

from fastapi import APIRouter

from app.schemas.posts import PostsUploadRequest, PostsUploadResponse
from app.services.post_ingestion import PostIngestionService
from app.services.storage import repository_bundle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostsUploadResponse)
async def upload_posts(
    payload: PostsUploadRequest,
) -> PostsUploadResponse:
    logger.info("Posts upload request received", extra={"topic": payload.topic})
    async with repository_bundle() as repositories:
        service = PostIngestionService(repositories.posts)
        result = await service.ingest_text(
            topic=payload.topic,
            custom_topic=payload.custom_topic,
            raw_text=payload.text,
        )
        await repositories.commit()
    return PostsUploadResponse(
        created_count=result.created_count,
        skipped_count=result.skipped_count,
    )
