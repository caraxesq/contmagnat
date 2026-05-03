from pydantic import BaseModel, Field


class PostsUploadRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1)
    custom_topic: str | None = Field(default=None, max_length=128)


class PostsUploadResponse(BaseModel):
    created_count: int
    skipped_count: int
