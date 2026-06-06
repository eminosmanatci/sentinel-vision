"""Abstract repository interfaces for SentinelVision domain.

Defines contracts for data access layer following the Repository
pattern. Enables dependency injection and test mocking.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import Detection, Video


class VideoRepository(ABC):
    """Abstract repository for Video entity operations."""

    @abstractmethod
    async def create(self, video: Video) -> Video:
        """Persist a new video record."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, video_id: UUID) -> Optional[Video]:
        """Retrieve a video by UUID."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, video: Video) -> Video:
        """Update an existing video record."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Video]:
        """List videos with pagination."""
        raise NotImplementedError


class DetectionRepository(ABC):
    """Abstract repository for Detection entity operations."""

    @abstractmethod
    async def create(self, detection: Detection) -> Detection:
        """Persist a single detection record."""
        raise NotImplementedError

    @abstractmethod
    async def create_batch(self, detections: list[Detection]) -> int:
        """Batch insert multiple detection records."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_video_id(self, video_id: UUID) -> list[Detection]:
        """Retrieve detections for a specific video."""
        raise NotImplementedError

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: list[float],
        video_id: Optional[UUID] = None,
        limit: int = 5,
    ) -> list[Detection]:
        """Vector similarity search via pgvector."""
        raise NotImplementedError

    @abstractmethod
    async def get_anomalies_by_video(
        self, video_id: UUID, limit: int = 100
    ) -> list[Detection]:
        """Retrieve anomaly detections for a video."""
        raise NotImplementedError