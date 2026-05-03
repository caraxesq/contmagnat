from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=64)
    user_request: str = Field(min_length=1)
    custom_topic: str | None = Field(default=None, max_length=128)


class GenerationResponse(BaseModel):
    status: str
    generated_text: str
