"""SQLAlchemy-based repository implementations for SentinelVision.

Provides async CRUD operations for Video and Detection entities,
including vector similarity search via pgvector and batch insertion
for high-throughput processing pipelines.
"""

from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.logging import logger
from app.domain.entities import Detection, Video, VideoStatus
from app.infrastructure.database.models import DetectionModel, VideoModel
from app.repositories.base import DetectionRepository, VideoRepository


class SQLVideoRepository(VideoRepository):
    """Async SQLAlchemy repository for Video entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, video: Video) -> Video:
        """Persist a new video record."""
        model = VideoModel(
            id=video.id,
            filename=video.filename,
            file_path=video.file_path,
            status=video.status.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return video

    async def get_by_id(self, video_id: UUID) -> Video | None:
        """Retrieve a video by its UUID."""
        result = await self._session.execute(
            select(VideoModel).where(VideoModel.id == video_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def update(self, video: Video) -> Video:
        """Update an existing video record."""
        result = await self._session.execute(
            select(VideoModel).where(VideoModel.id == video.id)
        )
        model = result.scalar_one()
        model.status = video.status.value
        model.duration_seconds = video.duration_seconds
        model.fps = video.fps
        model.resolution = video.resolution
        model.processed_at = video.processed_at
        await self._session.commit()
        return video

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Video]:
        """List videos with pagination, ordered by creation date."""
        result = await self._session.execute(
            select(VideoModel)
            .order_by(VideoModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(model: VideoModel) -> Video:
        """Convert SQLAlchemy model to domain entity."""
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


class SQLDetectionRepository(DetectionRepository):
    """Async SQLAlchemy repository for Detection entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, detection: Detection) -> Detection:
        """Persist a single detection record."""
        model = self._to_model(detection)
        self._session.add(model)
        await self._session.commit()
        return detection

    async def create_batch(self, detections: list[Detection]) -> int:
        """Batch insert multiple detection records efficiently."""
        if not detections:
            return 0

        values = [self._detection_to_dict(d) for d in detections]

        stmt = insert(DetectionModel).values(values)
        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(
            "Batch inserted detections successfully",
            extra={"count": len(detections)}
        )
        return len(detections)

    async def get_by_video_id(self, video_id: UUID) -> list[Detection]:
        """Retrieve all detections for a specific video."""
        result = await self._session.execute(
            select(DetectionModel)
            .where(DetectionModel.video_id == video_id)
            .order_by(DetectionModel.timestamp.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def search_similar(
        self,
        query_embedding: list[float],
        video_id: UUID | None = None,
        limit: int = 5,
    ) -> list[Detection]:
        """Find detections with semantically similar descriptions.
        Applies pre-filtering if video_id is provided, optimizing vector search.
        """
        stmt = select(DetectionModel)

        # 1. First apply logical filters (Pre-filtering)
        if video_id:
            stmt = stmt.where(DetectionModel.video_id == video_id)

        # 2. Then apply vector similarity sorting and limit
        stmt = (
            stmt.order_by(DetectionModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_anomalies_by_video(
        self, video_id: UUID, limit: int = 100
    ) -> list[Detection]:
        """Retrieve anomaly detections for a specific video."""
        result = await self._session.execute(
            select(DetectionModel)
            .where(
                DetectionModel.video_id == video_id,
                DetectionModel.is_anomaly.is_(True),
            )
            .order_by(DetectionModel.timestamp.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_model(detection: Detection) -> DetectionModel:
        """Convert domain entity to SQLAlchemy model."""
        return DetectionModel(
            id=detection.id,
            video_id=detection.video_id,
            timestamp=detection.timestamp,
            frame_number=detection.frame_number,
            object_class=detection.object_class,
            confidence=detection.confidence,
            bbox_x1=detection.bbox_x1,
            bbox_y1=detection.bbox_y1,
            bbox_x2=detection.bbox_x2,
            bbox_y2=detection.bbox_y2,
            description=detection.description,
            is_anomaly=detection.is_anomaly,
            anomaly_type=(
                detection.anomaly_type.value
                if detection.anomaly_type
                else ""
            ),
            embedding=detection.embedding,
        )

    @staticmethod
    def _to_entity(model: DetectionModel) -> Detection:
        """Convert SQLAlchemy model to domain entity."""
        from app.domain.entities import AnomalyType

        anomaly_type = AnomalyType.NONE
        if model.anomaly_type:
            try:
                anomaly_type = AnomalyType(model.anomaly_type)
            except ValueError:
                anomaly_type = AnomalyType.NONE

        return Detection(
            id=model.id,
            video_id=model.video_id,
            timestamp=model.timestamp,
            frame_number=model.frame_number,
            object_class=model.object_class,
            confidence=model.confidence,
            bbox_x1=model.bbox_x1,
            bbox_y1=model.bbox_y1,
            bbox_x2=model.bbox_x2,
            bbox_y2=model.bbox_y2,
            description=model.description,
            is_anomaly=model.is_anomaly,
            anomaly_type=anomaly_type,
            embedding=model.embedding,
        )

    @staticmethod
    def _detection_to_dict(detection: Detection) -> dict:
        """Serialize Detection entity to dict for batch insert."""
        return {
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
            "anomaly_type": (
                detection.anomaly_type.value
                if detection.anomaly_type
                else ""
            ),
            "embedding": detection.embedding,
        }