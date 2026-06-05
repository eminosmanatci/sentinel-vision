import os
from uuid import UUID

from app.core.exceptions import ProcessingError
from app.core.logging import logger
from app.domain.entities import AnomalyType, Detection, VideoStatus
from app.infrastructure.ai.anomaly_engine import AnomalyEngine, DetectionContext
from app.infrastructure.ai.openai_service import OpenAIService
from app.infrastructure.ai.yolo_service import YOLOService
from app.repositories.base import DetectionRepository, VideoRepository


class ProcessingService:
    def __init__(
        self,
        video_repo: VideoRepository,
        detection_repo: DetectionRepository,
    ) -> None:
        self._video_repo = video_repo
        self._detection_repo = detection_repo
        self._yolo = YOLOService()
        self._openai = OpenAIService()
        self._anomaly = AnomalyEngine()

    async def process_video(self, video_id: UUID) -> None:
        logger.info(f"Starting processing for video: {video_id}")

        video = await self._video_repo.get_by_id(video_id)
        if not video:
            raise ProcessingError(f"Video not found: {video_id}")

        if not os.path.exists(video.file_path):
            raise ProcessingError(f"Video file not found: {video.file_path}")

        video.mark_processing()
        await self._video_repo.update(video)

        try:
            cap_props = self._get_video_properties(video.file_path)
            video.duration_seconds = cap_props["duration"]
            video.fps = cap_props["fps"]
            video.resolution = cap_props["resolution"]

            await self._video_repo.update(video)

            frame_count = 0
            for frame, frame_num, timestamp in self._yolo.extract_frames(
                video.file_path, interval_seconds=1
            ):
                detections = self._yolo.detect_objects(frame)

                if detections:
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

                        await self._detection_repo.create(detection)

                frame_count += 1

            video.mark_completed()
            await self._video_repo.update(video)
            logger.info(f"Processing completed for video: {video_id}. Frames: {frame_count}")

        except Exception as e:
            logger.error(f"Processing failed for {video_id}: {e}")
            video.mark_failed()
            await self._video_repo.update(video)
            raise ProcessingError(f"Video processing failed: {e}")

    def _get_video_properties(self, video_path: str) -> dict:
        import cv2

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        return {
            "fps": fps,
            "duration": total_frames / fps if fps > 0 else 0,
            "resolution": f"{width}x{height}",
        }