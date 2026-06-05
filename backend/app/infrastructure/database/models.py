import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship

from app.domain.entities import AnomalyType, VideoStatus

Base = declarative_base()


class VideoModel(Base):
    __tablename__ = "videos"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, default=0.0)
    fps = Column(Float, default=0.0)
    resolution = Column(String(20), default="")
    status = Column(String(20), default=VideoStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    detections = relationship("DetectionModel", back_populates="video", cascade="all, delete-orphan")


class DetectionModel(Base):
    __tablename__ = "detections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(PGUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    object_class = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    description = Column(String(1000), default="")
    is_anomaly = Column(Boolean, default=False)
    anomaly_type = Column(String(50), default="")
    embedding = Column(Vector(1536), nullable=True)

    video = relationship("VideoModel", back_populates="detections")