"""Celery background tasks for video processing."""

from contextlib import contextmanager
from typing import Generator
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.domain.entities import Video, VideoStatus
from app.infrastructure.database.models import DetectionModel, VideoModel

# Import celery_app - this works because celery_app.py no longer imports video_tasks
# at module level (it imports it AFTER celery_app is created)
from app.infrastructure.tasks.celery_app import celery_app
from app.services.processing_service import ProcessingService

# =============================================================================
# Database Configuration
# =============================================================================

SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")

_sync_engine = create_engine(
    SYNC_DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    echo=False,
)
SyncSession = sessionmaker(bind=_sync_engine, expire_on_commit=False)


# =============================================================================
# Repository Pattern (Sync Adapters)
# =============================================================================

class SyncVideoRepository:
    """Synchronous video repository for Celery worker context."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, video_id: UUID) -> Video | None:
        """Retrieve video by UUID."""
        model = (
            self._session.query(VideoModel)
            .filter_by(id=video_id)
            .first()
        )
        if not model:
            return None
        
        return Video(
            id=model.id,
            filename=model.filename,
            file_path=model.file_path,
            duration_seconds=model.duration_seconds,
            fps=model.fps,
            resolution=model.resolution,
            status=VideoStatus(model.status),
            created_at=model.created_at,
            processed_at=model.processed_at,
        )

    def update(self, video: Video) -> Video:
        """Persist video metadata changes."""
        model = (
            self._session.query(VideoModel)
            .filter_by(id=video.id)
            .first()
        )
        if not model:
            raise ProcessingError(f"Video model not found for update: {video.id}")

        model.status = video.status.value
        model.duration_seconds = video.duration_seconds
        model.fps = video.fps
        model.resolution = video.resolution
        model.processed_at = video.processed_at
        
        self._session.commit()
        return video


class SyncDetectionRepository:
    """Synchronous detection repository with batch insert support."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_batch(self, detections: list) -> int:
        """Batch insert detections with proper embedding handling."""
        if not detections:
            return 0

        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from app.domain.entities import AnomalyType

        values = []
        for detection in detections:
            anomaly_value = (
                detection.anomaly_type.value 
                if detection.anomaly_type 
                else None
            )
            
            embedding_value = detection.embedding
            if isinstance(embedding_value, str):
                import json
                embedding_value = json.loads(embedding_value)
            
            values.append({
                "id": str(detection.id),
                "video_id": str(detection.video_id),
                "timestamp": detection.timestamp,
                "frame_number": detection.frame_number,
                "object_class": detection.object_class,
                "confidence": detection.confidence,
                "bbox_x1": detection.bbox_x1,
                "bbox_y1": detection.bbox_y1,
                "bbox_x2": detection.bbox_x2,
                "bbox_y2": detection.bbox_y2,
                "description": detection.description,
                "is_anomaly": detection.is_anomaly,
                "anomaly_type": anomaly_value,
                "embedding": embedding_value,
            })

        try:
            self._session.execute(pg_insert(DetectionModel), values)
            self._session.commit()
            return len(values)
        except Exception as exc:
            self._session.rollback()
            logger.error(
                "Batch insert failed, rolling back",
                extra={
                    "batch_size": len(values),
                    "error": str(exc),
                },
            )
            raise ProcessingError(f"Detection batch insert failed: {exc}") from exc


# =============================================================================
# Session Management
# =============================================================================

@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Context manager for sync database sessions with automatic cleanup."""
    session = SyncSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# =============================================================================
# Celery Task
# =============================================================================

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ProcessingError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_video_task(self, video_id: str) -> dict:
    """Process uploaded video through AI pipeline."""
    logger.info(
        "Celery task initiated",
        extra={
            "video_id": video_id,
            "task_id": self.request.id,
            "attempt": self.request.retries,
        },
    )

    try:
        with get_sync_session() as session:
            video_repo = SyncVideoRepository(session)
            detection_repo = SyncDetectionRepository(session)
            
            service = ProcessingService(
                video_repo=video_repo,
                detection_repo=detection_repo,
                sync_mode=True,
            )
            
            frame_count = service.process_video_sync(UUID(video_id))
            
            logger.info(
                "Processing pipeline completed successfully",
                extra={
                    "video_id": video_id,
                    "frames_processed": frame_count,
                    "task_id": self.request.id,
                },
            )
            
            return {
                "status": "completed",
                "video_id": video_id,
                "frames_processed": frame_count,
                "task_id": self.request.id,
            }

    except ProcessingError as exc:
        logger.error(
            "Processing failed with business error",
            extra={
                "video_id": video_id,
                "error": str(exc),
                "retry_count": self.request.retries,
            },
        )
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception(
            "Unexpected error in video processing pipeline",
            extra={
                "video_id": video_id,
                "error_type": type(exc).__name__,
            },
        )
        raise self.retry(exc=exc)