"""SQLAlchemy ORM models for SentinelVision database.

Defines table schemas with pgvector extension support for
1536-dimensional OpenAI embedding vectors.
"""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector  # pip install pgvector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    event, # Eklendi
    text,  # Eklendi
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# PostgreSQL'de vector extension'ının aktif olduğundan emin ol
@event.listens_for(Base.metadata, 'before_create')
def create_vector_extension(target, connection, **kw):
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))


class VideoModel(Base):
    """Video metadata table."""

    __tablename__ = "videos"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    duration_seconds = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)


class DetectionModel(Base):
    """AI detection results table with vector embeddings."""

    __tablename__ = "detections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    object_class = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    is_anomaly = Column(Boolean, default=False, nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=True)

    # pgvector embedding: 1536 dimensions for text-embedding-3-small
    embedding = Column(Vector(1536), nullable=True)

    # Let PostgreSQL handle the timestamp via server_default
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )