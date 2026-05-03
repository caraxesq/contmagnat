import argparse
import asyncio
from pathlib import Path

from app.db.repositories.posts import PostsRepository
from app.db.session import AsyncSessionLocal
from app.services.post_ingestion import PostIngestionService


async def import_posts(topic: str, path: Path, custom_topic: str | None) -> None:
    async with AsyncSessionLocal() as session:
        service = PostIngestionService(PostsRepository(session))
        result = await service.ingest_text(
            topic=topic,
            custom_topic=custom_topic,
            raw_text=path.read_text(encoding="utf-8"),
        )
        await session.commit()
    print(f"Created: {result.created_count}. Skipped: {result.skipped_count}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import style posts from a text file.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--custom-topic")
    args = parser.parse_args()

    asyncio.run(import_posts(args.topic, args.file, args.custom_topic))


if __name__ == "__main__":
    main()
