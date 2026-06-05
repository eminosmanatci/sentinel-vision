from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Detection, Video, VideoStatus
from app.infrastructure.database.models import DetectionModel, VideoModel
from app.repositories.base import DetectionRepository, VideoRepository


class SQLVideoRepository(VideoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, video: Video) -> Video:
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

    async def get_by_id(self, video_id: UUID) -> Optional[Video]:
        result = await self._session.execute(
            select(VideoModel).where(VideoModel.id == video_id)
        )
        model = result.scalar_one_or_none()
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

    async def update(self, video: Video) -> Video:
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
        result = await self._session.execute(
            select(VideoModel).order_by(VideoModel.created_at.desc()).limit(limit).offset(offset)
        )
        models = result.scalars().all()
        return [
            Video(
                id=m.id,
                filename=m.filename,
                file_path=m.file_path,
                duration_seconds=m.duration_seconds,
                fps=m.fps,
                resolution=m.resolution,
                status=VideoStatus(m.status),
                created_at=m.created_at,
                processed_at=m.processed_at,
            )
            for m in models
        ]


class SQLDetectionRepository(DetectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, detection: Detection) -> Detection:
        model = DetectionModel(
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
            anomaly_type=detection.anomaly_type.value,
            embedding=detection.embedding,
        )
        self._session.add(model)
        await self._session.commit()
        return detection

    async def get_by_video_id(self, video_id: UUID) -> list[Detection]:
        result = await self._session.execute(
            select(DetectionModel).where(DetectionModel.video_id == video_id)
        )
        models = result.scalars().all()
        return [
            Detection(
                id=m.id,
                video_id=m.video_id,
                timestamp=m.timestamp,
                frame_number=m.frame_number,
                object_class=m.object_class,
                confidence=m.confidence,
                bbox_x1=m.bbox_x1,
                bbox_y1=m.bbox_y1,
                bbox_x2=m.bbox_x2,
                bbox_y2=m.bbox_y2,
                description=m.description,
                is_anomaly=m.is_anomaly,
                anomaly_type=m.anomaly_type,
                embedding=m.embedding,
            )
            for m in models
        ]

    async def search_similar(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[Detection]:
        # pgvector cosine similarity search
        result = await self._session.execute(
            select(DetectionModel)
            .order_by(DetectionModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        models = result.scalars().all()
        return [
            Detection(
                id=m.id,
                video_id=m.video_id,
                timestamp=m.timestamp,
                frame_number=m.frame_number,
                object_class=m.object_class,
                confidence=m.confidence,
                description=m.description,
                is_anomaly=m.is_anomaly,
                anomaly_type=m.anomaly_type,
                embedding=m.embedding,
            )
            for m in models
        ]