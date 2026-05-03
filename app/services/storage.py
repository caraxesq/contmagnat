from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.core.config import get_settings
from app.db.file_storage import FileGenerationLogsRepository, FilePostsRepository
from app.db.memory import generation_logs_repository, posts_repository


@dataclass
class RepositoryBundle:
    posts: object
    generation_logs: object
    commit: object


async def _noop_commit() -> None:
    return None


@asynccontextmanager
async def repository_bundle() -> AsyncIterator[RepositoryBundle]:
    settings = get_settings()
    if settings.storage_backend == "memory":
        yield RepositoryBundle(
            posts=posts_repository,
            generation_logs=generation_logs_repository,
            commit=_noop_commit,
        )
        return

    if settings.storage_backend == "file":
        yield RepositoryBundle(
            posts=FilePostsRepository(settings.training_data_dir),
            generation_logs=FileGenerationLogsRepository(settings.training_data_dir),
            commit=_noop_commit,
        )
        return

    from app.db.repositories.generation_logs import GenerationLogsRepository
    from app.db.repositories.posts import PostsRepository
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield RepositoryBundle(
            posts=PostsRepository(session),
            generation_logs=GenerationLogsRepository(session),
            commit=session.commit,
        )
