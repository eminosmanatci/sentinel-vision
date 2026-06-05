from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnomalyType(str, Enum):
    NIGHT_INTRUSION = "night_intrusion"
    RESTRICTED_ZONE = "restricted_zone_entry"
    ABANDONED_OBJECT = "abandoned_object"
    SUSPICIOUS_LOITERING = "suspicious_loitering"
    NONE = "none"


@dataclass
class Video:
    id: UUID = field(default_factory=uuid4)
    filename: str = ""
    file_path: str = ""
    duration_seconds: float = 0.0
    fps: float = 0.0
    resolution: str = ""
    status: VideoStatus = VideoStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    def mark_processing(self) -> None:
        self.status = VideoStatus.PROCESSING

    def mark_completed(self) -> None:
        self.status = VideoStatus.COMPLETED
        self.processed_at = datetime.utcnow()

    def mark_failed(self) -> None:
        self.status = VideoStatus.FAILED


@dataclass
class Detection:
    id: UUID = field(default_factory=uuid4)
    video_id: UUID = field(default_factory=uuid4)
    timestamp: float = 0.0
    frame_number: int = 0
    object_class: str = ""
    confidence: float = 0.0
    bbox_x1: float = 0.0
    bbox_y1: float = 0.0
    bbox_x2: float = 0.0
    bbox_y2: float = 0.0
    description: str = ""
    is_anomaly: bool = False
    anomaly_type: AnomalyType = AnomalyType.NONE
    embedding: Optional[list[float]] = None