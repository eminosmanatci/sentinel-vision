"""Pydantic schemas for video API responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VideoResponse(BaseModel):
    """Video metadata response schema."""
    
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    duration_seconds: float | None = None
    fps: float | None = None
    resolution: str | None = None
    status: str
    created_at: datetime | None = None  # HATA ÇÖZÜMÜ: Artık zorunlu değil
    processed_at: datetime | None = None


class VideoListResponse(BaseModel):
    """Paginated video list response."""
    
    items: list[VideoResponse]
    total: int


class VideoUploadResponse(BaseModel):
    """Video upload confirmation response."""
    
    id: UUID
    filename: str
    status: str
    message: str
    task_id: str | None = None