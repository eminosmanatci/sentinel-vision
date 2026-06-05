"""Celery background tasks for video processing pipeline.

Handles async video analysis using YOLOv8, OpenAI embeddings,
and anomaly detection with proper error handling and retries.
"""

import asyncio
from uuid import UUID

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.infrastructure.database.repositories import SQLDetectionRepository, SQLVideoRepository
from app.services.processing_service import ProcessingService

# Create dedicated engine for Celery workers (separate from FastAPI)
_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
)
AsyncSessionLocal = sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ProcessingError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_video_task(self, video_id: str) -> dict:
    """Process a security video through the AI analysis pipeline.

    This task runs the full processing chain:
    1. Extract frames from video
    2. Run YOLOv8 object detection
    3. Generate descriptions via OpenAI
    4. Create vector embeddings
    5. Run anomaly detection rules
    6. Persist results to PostgreSQL + pgvector

    Args:
        video_id: UUID string of the video to process.

    Returns:
        dict with status and processed frame count.

    Raises:
        self.retry: On recoverable errors with exponential backoff.
    """
    logger.info(
        "Celery task started for video processing",
        extra={
            "video_id": video_id,
            "task_id": self.request.id,
            "attempt": self.request.retries + 1,
        },
    )

    async def _run_pipeline() -> dict:
        """Execute the async processing pipeline with isolated session."""
        async with AsyncSessionLocal() as session:
            video_repo = SQLVideoRepository(session)
            detection_repo = SQLDetectionRepository(session)

            service = ProcessingService(
                video_repo=video_repo,
                detection_repo=detection_repo,
            )

            frame_count = await service.process_video(UUID(video_id))
            return {"status": "completed", "video_id": video_id, "frames_processed": frame_count}

    # Celery runs synchronously — create event loop for async code
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run_pipeline())
        loop.close()

        logger.info(
            "Video processing completed successfully",
            extra={
                "video_id": video_id,
                "task_id": self.request.id,
                "frames_processed": result.get("frames_processed", 0),
            },
        )
        return result

    except ProcessingError as exc:
        logger.error(
            f"Processing failed for video {video_id}: {exc}",
            extra={"video_id": video_id, "task_id": self.request.id},
        )
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception(
            f"Unexpected error processing video {video_id}",
            extra={"video_id": video_id, "task_id": self.request.id},
        )
        raise self.retry(exc=exc)

    finally:
        # Cleanup: close the event loop
        try:
            loop.close()
        except Exception:
            pass