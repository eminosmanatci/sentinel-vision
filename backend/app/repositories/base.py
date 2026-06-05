from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import Video, Detection


class VideoRepository(ABC):
    @abstractmethod
    async def create(self, video: Video) -> Video:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, video_id: UUID) -> Optional[Video]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, video: Video) -> Video:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Video]:
        raise NotImplementedError


class DetectionRepository(ABC):
    @abstractmethod
    async def create(self, detection: Detection) -> Detection:
        raise NotImplementedError

    @abstractmethod
    async def get_by_video_id(self, video_id: UUID) -> list[Detection]:
        raise NotImplementedError

    @abstractmethod
    async def search_similar(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[Detection]:
        raise NotImplementedError