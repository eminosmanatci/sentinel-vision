import os
from pathlib import Path
from typing import Generator

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.config import settings
from app.core.logging import logger


class YOLOService:
    def __init__(self) -> None:
        self._model = None
        self._model_name = "yolov8n.pt"

    def _load_model(self) -> YOLO:
        if self._model is None:
            logger.info(f"Loading YOLO model: {self._model_name}")
            self._model = YOLO(self._model_name)
        return self._model

    def extract_frames(
        self, video_path: str, interval_seconds: int = 1
    ) -> Generator[tuple[np.ndarray, int, float], None, None]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        frame_interval = int(fps * interval_seconds)
        frame_count = 0
        processed_count = 0

        logger.info(f"Video info: {fps:.2f} fps, {total_frames} frames, {duration:.2f}s")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps if fps > 0 else 0
                processed_count += 1
                yield frame, frame_count, timestamp

            frame_count += 1

        cap.release()
        logger.info(f"Extracted {processed_count} frames from {video_path}")

    def detect_objects(
        self, frame: np.ndarray
    ) -> list[dict]:
        model = self._load_model()
        results = model(frame, verbose=False)

        detections = []
        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                detections.append({
                    "class_name": model.names[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                    },
                })

        return detections