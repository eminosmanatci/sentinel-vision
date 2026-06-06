"""Video processing service with synchronous pipeline execution.

Orchestrates YOLOv8 detection, OpenAI NLP, anomaly detection,
and database persistence for security video analytics.
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import cv2
import numpy as np

from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.domain.entities import AnomalyType, Detection, VideoStatus
from app.infrastructure.ai.anomaly_engine import AnomalyEngine, DetectionContext
from app.infrastructure.ai.openai_service import OpenAIService
from app.infrastructure.ai.yolo_service import YOLOService


@dataclass(frozen=True)
class VideoProperties:
    """Immutable video metadata extracted via OpenCV."""
    fps: float
    duration: float
    resolution: str
    total_frames: int


class ProcessingService:
    """Video processing pipeline with sync/async repository support."""

    # Batch size for detection persistence to optimize DB writes
    DETECTION_BATCH_SIZE: int = 10
    FRAME_INTERVAL_SECONDS: int = 1

    def __init__(
        self,
        video_repo: Any,
        detection_repo: Any,
        sync_mode: bool = False,
    ) -> None:
        self._video_repo = video_repo
        self._detection_repo = detection_repo
        self._sync_mode = sync_mode
        self._yolo = YOLOService()
        self._openai = OpenAIService()
        self._anomaly = AnomalyEngine()

    def process_video_sync(self, video_id: UUID) -> int:
        """Execute full processing pipeline synchronously."""
        logger.info(
            "Starting video processing pipeline",
            extra={"video_id": str(video_id), "mode": "sync"},
        )

        video = self._video_repo.get_by_id(video_id)
        if not video:
            raise ProcessingError(f"Video not found: {video_id}")

        if not os.path.exists(video.file_path):
            raise ProcessingError(f"Video file missing: {video.file_path}")

        video.mark_processing()
        self._video_repo.update(video)

        try:
            props = self._get_video_properties(video.file_path)
            video.duration_seconds = props.duration
            video.fps = props.fps
            video.resolution = props.resolution
            self._video_repo.update(video)

            frame_count = 0
            batch_detections: list[Detection] = []

            for frame, frame_num, timestamp in self._yolo.extract_frames(
                video.file_path,
                interval_seconds=self.FRAME_INTERVAL_SECONDS,
            ):
                detections = self._yolo.detect_objects(frame)

                if detections:
                    # Safely run async OpenAI calls inside a sync loop
                    description, embedding = asyncio.run(
                        self._get_ai_insights(timestamp, detections)
                    )

                    if isinstance(embedding, np.ndarray):
                        embedding = embedding.tolist()

                    for det in detections:
                        ctx = DetectionContext(
                            timestamp=timestamp,
                            object_class=det["class_name"],
                            bbox=det["bbox"],
                        )
                        is_anomaly, anomaly_type = self._anomaly.check_anomaly(ctx)

                        batch_detections.append(
                            Detection(
                                video_id=video_id,
                                timestamp=timestamp,
                                frame_number=frame_num,
                                object_class=det["class_name"],
                                confidence=det["confidence"],
                                bbox_x1=det["bbox"]["x1"],
                                bbox_y1=det["bbox"]["y1"],
                                bbox_x2=det["bbox"]["x2"],
                                bbox_y2=det["bbox"]["y2"],
                                description=description,
                                is_anomaly=is_anomaly,
                                anomaly_type=anomaly_type,
                                embedding=embedding,
                            )
                        )

                frame_count += 1

                if len(batch_detections) >= self.DETECTION_BATCH_SIZE:
                    self._flush_detections(batch_detections)
                    batch_detections.clear()

            # Flush remaining detections
            if batch_detections:
                self._flush_detections(batch_detections)

            video.mark_completed()
            self._video_repo.update(video)

            logger.info(
                "Pipeline completed successfully",
                extra={
                    "video_id": str(video_id),
                    "frames_processed": frame_count,
                },
            )
            return frame_count

        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}", exc_info=True)
            video.mark_failed()
            self._video_repo.update(video)
            raise ProcessingError(f"Video processing failed: {exc}") from exc

    async def _get_ai_insights(self, timestamp: float, detections: list) -> tuple[str, list]:
        """Helper to run OpenAI requests concurrently for faster processing."""
        # Use asyncio.gather to call description and embedding concurrently if needed,
        # but since embedding requires description, we await them sequentially here.
        description = await self._openai.generate_description(timestamp, detections)
        embedding = await self._openai.create_embedding(description)
        return description, embedding

    def _get_video_properties(self, video_path: str) -> VideoProperties:
        """Extract video metadata using OpenCV."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ProcessingError(f"Cannot open video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if fps <= 0:
                fps = 30.0

            return VideoProperties(
                fps=fps,
                duration=total_frames / fps,
                resolution=f"{width}x{height}",
                total_frames=total_frames,
            )
        finally:
            cap.release()

    def _flush_detections(self, detections: list[Detection]) -> None:
        """Persist detection batch with error handling."""
        if not detections:
            return

        try:
            inserted = self._detection_repo.create_batch(detections)
            logger.debug(
                "Detection batch flushed",
                extra={"batch_size": inserted},
            )
        except Exception as exc:
            logger.error(f"Failed to flush detection batch: {exc}")
            raise