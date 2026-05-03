from fastapi import FastAPI

from app.api.routes.generation import router as generation_router
from app.api.routes.health import router as health_router
from app.api.routes.posts import router as posts_router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Contmagnat RAG Generator", version="0.1.0")
    app.include_router(health_router)
    app.include_router(posts_router)
    app.include_router(generation_router)
    return app


app = create_app()
