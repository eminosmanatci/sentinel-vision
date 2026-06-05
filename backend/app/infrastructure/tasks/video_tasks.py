import asyncio
from uuid import UUID

from app.core.logging import logger
from app.infrastructure.database.repositories import (
    SQLDetectionRepository,
    SQLVideoRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.tasks.celery_app import celery_app
from app.services.processing_service import ProcessingService


@celery_app.task(bind=True, max_retries=3)
def process_video_task(self, video_id: str) -> dict:
    logger.info(f"Celery task started for video: {video_id}")

    async def _run():
        async with AsyncSessionLocal() as session:
            video_repo = SQLVideoRepository(session)
            detection_repo = SQLDetectionRepository(session)
            service = ProcessingService(video_repo, detection_repo)
            await service.process_video(UUID(video_id))

    try:
        asyncio.run(_run())
        return {"status": "completed", "video_id": video_id}
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)