from uuid import UUID

from pydantic import BaseModel


class DetectionResponse(BaseModel):
    id: UUID
    timestamp: float
    frame_number: int
    object_class: str
    confidence: float
    description: str
    is_anomaly: bool
    anomaly_type: str


class DetectionListResponse(BaseModel):
    items: list[DetectionResponse]
    total: int