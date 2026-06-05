from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    message: str = "Video uploaded successfully. Processing started."


class VideoResponse(BaseModel):
    id: UUID
    filename: str
    duration_seconds: float
    fps: float
    resolution: str
    status: str
    created_at: datetime
    processed_at: datetime | None


class VideoListResponse(BaseModel):
    items: list[VideoResponse]
    total: int