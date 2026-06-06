import os
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import StorageError, ValidationError
from app.core.logging import logger
from app.domain.entities import Video, VideoStatus
from app.repositories.base import VideoRepository


class VideoService:
    def __init__(self, video_repo: VideoRepository) -> None:
        self._repo = video_repo

    async def create_upload(self, filename: str) -> Video:
        video_id = uuid4()
        # İndirme klasörünü oluştur
        upload_dir = Path(settings.UPLOAD_DIR) / str(video_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = str(upload_dir / "video.mp4")

        video = Video(
            id=video_id,
            filename=filename,
            file_path=file_path,
            status=VideoStatus.PENDING,
        )

        await self._repo.create(video)
        logger.info(f"Video created: {video_id} - {filename}")
        return video

    async def get_video(self, video_id: UUID) -> Video | None:
        return await self._repo.get_by_id(video_id)

    async def list_videos(self, limit: int = 50, offset: int = 0) -> list[Video]:
        return await self._repo.list_all(limit=limit, offset=offset)

    def validate_file(self, filename: str, size: int) -> None:
        # Uzantı kontrolü
        ext = Path(filename).suffix.lower()
        if ext not in settings.SUPPORTED_VIDEO_FORMATS:
            raise ValidationError(f"Unsupported format: {ext}. Use: {settings.SUPPORTED_VIDEO_FORMATS}")

        # Boyut kontrolü (varsayılan 500MB)
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 500 * 1024 * 1024)
        if size > max_size:
            raise ValidationError(f"File too large: {size} bytes. Max: {max_size} bytes")