from uuid import UUID

from app.core.logging import logger
from app.repositories.base import DetectionRepository, VideoRepository


class ProcessingService:
    def __init__(
        self,
        video_repo: VideoRepository,
        detection_repo: DetectionRepository,
    ) -> None:
        self._video_repo = video_repo
        self._detection_repo = detection_repo

    async def start_processing(self, video_id: UUID) -> None:
        """Trigger background processing. Implementation in Adım 3."""
        logger.info(f"Processing queued for video: {video_id}")
        # Celery task will be called here
        pass