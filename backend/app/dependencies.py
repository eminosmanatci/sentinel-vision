from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories import (
    SQLDetectionRepository,
    SQLVideoRepository,
    get_db,
)
from app.repositories.base import DetectionRepository, VideoRepository
from app.services.video_service import VideoService
from app.services.processing_service import ProcessingService


async def get_video_repository(
    session: AsyncSession = Depends(get_db),
) -> VideoRepository:
    return SQLVideoRepository(session)


async def get_detection_repository(
    session: AsyncSession = Depends(get_db),
) -> DetectionRepository:
    return SQLDetectionRepository(session)


async def get_video_service(
    video_repo: VideoRepository = Depends(get_video_repository),
) -> VideoService:
    return VideoService(video_repo)


async def get_processing_service(
    video_repo: VideoRepository = Depends(get_video_repository),
    detection_repo: DetectionRepository = Depends(get_detection_repository),
) -> ProcessingService:
    return ProcessingService(video_repo, detection_repo)