"""Video processing service for SentinelVision AI analytics.

Orchestrates the complete pipeline: frame extraction, object detection,
description generation, embedding creation, anomaly detection,
and batched database persistence.
"""

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import cv2

from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.domain.entities import AnomalyType, Detection, VideoStatus
from app.infrastructure.ai.anomaly_engine import AnomalyEngine, DetectionContext
from app.infrastructure.ai.openai_service import OpenAIService
from app.infrastructure.ai.yolo_service import YOLOService
from app.infrastructure.database.repositories import (
    SQLDetectionRepository,
    SQLVideoRepository,
)


@dataclass(frozen=True)
class VideoProperties:
    """Immutable video metadata container."""

    fps: float
    duration: float
    resolution: str
    total_frames: int


class ProcessingService:
    """Service responsible for AI-powered video analysis pipeline.

    Processes security footage through YOLOv8 detection, OpenAI NLP,
    vector embeddings, and rule-based anomaly detection.
    """

    def __init__(
        self,
        video_repo: SQLVideoRepository,
        detection_repo: SQLDetectionRepository,
    ) -> None:
        self._video_repo = video_repo
        self._detection_repo = detection_repo
        self._yolo = YOLOService()
        self._openai = OpenAIService()
        self._anomaly = AnomalyEngine()

    async def process_video(self, video_id: UUID) -> int:
        """Execute the full video processing pipeline.

        Args:
            video_id: UUID of the video to process.

        Returns:
            int: Number of frames processed.

        Raises:
            ProcessingError: If video file is missing or processing fails.
        """
        logger.info("Starting video processing pipeline", extra={"video_id": str(video_id)})

        video = await self._video_repo.get_by_id(video_id)
        if not video:
            raise ProcessingError(f"Video not found: {video_id}")

        if not os.path.exists(video.file_path):
            raise ProcessingError(f"Video file not found on disk: {video.file_path}")

        # Update status to processing
        video.mark_processing()
        await self._video_repo.update(video)

        try:
            props = self._get_video_properties(video.file_path)
            video.duration_seconds = props.duration
            video.fps = props.fps
            video.resolution = props.resolution
            await self._video_repo.update(video)

            frame_count = 0
            batch_detections: list[Detection] = []

            # Process frames with 1-second intervals
            for frame, frame_num, timestamp in self._yolo.extract_frames(
                video.file_path,
                interval_seconds=1,
            ):
                detections = self._yolo.detect_objects(frame)

                if detections:
                    # Batch OpenAI calls: one per frame, not per detection
                    description = await self._openai.generate_description(
                        timestamp=timestamp,
                        objects=detections,
                    )
                    embedding = await self._openai.create_embedding(description)

                    for det in detections:
                        ctx = DetectionContext(
                            timestamp=timestamp,
                            object_class=det["class_name"],
                            bbox=det["bbox"],
                        )
                        is_anomaly, anomaly_type = self._anomaly.check_anomaly(ctx)

                        detection = Detection(
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
                        batch_detections.append(detection)

                frame_count += 1

                # Batch insert every 10 frames to reduce DB round-trips
                if len(batch_detections) >= 10:
                    await self._detection_repo.create_batch(batch_detections)
                    batch_detections.clear()

            # Insert remaining detections
            if batch_detections:
                await self._detection_repo.create_batch(batch_detections)

            # Mark video as completed
            video.mark_completed()
            await self._video_repo.update(video)

            logger.info(
                "Video processing completed successfully",
                extra={
                    "video_id": str(video_id),
                    "frames_processed": frame_count,
                    "total_detections": frame_count,  # Approximate
                },
            )
            return frame_count

        except Exception as exc:
            logger.error(
                f"Video processing failed: {exc}",
                extra={"video_id": str(video_id)},
                exc_info=True,
            )
            video.mark_failed()
            await self._video_repo.update(video)
            raise ProcessingError(f"Video processing failed: {exc}") from exc

    def _get_video_properties(self, video_path: str) -> VideoProperties:
        """Extract video metadata using OpenCV.

        Args:
            video_path: Path to the video file.

        Returns:
            VideoProperties with fps, duration, resolution, and frame count.
        """
        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            return VideoProperties(
                fps=fps,
                duration=total_frames / fps if fps > 0 else 0.0,
                resolution=f"{width}x{height}",
                total_frames=total_frames,
            )
        finally:
            cap.release()