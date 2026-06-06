"""YOLOv8 object detection service for security footage analysis."""

import os
from pathlib import Path
from typing import Generator

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from app.core.config import settings
from app.core.logging import logger


# GLOBAL FIX: PyTorch 2.6+ weights_only bypass
# Must be set BEFORE any torch.load calls
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

# Also patch torch.load globally
_original_torch_load = torch.load


def _patched_torch_load(*args, **kwargs):
    """Force weights_only=False for all torch.load calls."""
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_torch_load


class YOLOService:
    """YOLOv8-based object detection service."""

    CONFIDENCE_THRESHOLD: float = 0.5
    TARGET_CLASSES: set[str] = {
        "person", "car", "truck", "bus", "motorcycle", "bicycle",
        "backpack", "handbag", "suitcase", "knife", "gun",
    }

    def __init__(self) -> None:
        self._model: YOLO | None = None
        self._model_name: str = "yolov8n.pt"
        self._model_path: Path = Path.home() / ".ultralytics" / self._model_name

    def _load_model(self) -> YOLO:
        """Lazy-load YOLOv8 model with PyTorch 2.6+ compatibility."""
        if self._model is not None:
            return self._model

        logger.info(
            "Loading YOLO model",
            extra={"model": self._model_name, "cached": self._model_path.exists()},
        )

        # Ensure patch is active
        torch.load = _patched_torch_load

        model_source = str(self._model_path) if self._model_path.exists() else self._model_name
        self._model = YOLO(model_source, verbose=False)
        logger.info("YOLO model loaded successfully")
        return self._model

    def extract_frames(
        self,
        video_path: str,
        interval_seconds: float = 1.0,
    ) -> Generator[tuple[np.ndarray, int, float], None, None]:
        """Extract frames from video at specified intervals."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0

            frame_interval = max(1, int(fps * interval_seconds))
            frame_num = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_num % frame_interval == 0:
                    yield frame, frame_num, frame_num / fps

                frame_num += 1

            logger.info(
                "Frame extraction completed",
                extra={
                    "total_frames": frame_num,
                    "extracted": frame_num // frame_interval,
                },
            )
        finally:
            cap.release()

    def detect_objects(self, frame: np.ndarray) -> list[dict]:
        """Run YOLOv8 inference on a single frame."""
        model = self._load_model()
        height, width = frame.shape[:2]

        # Use torch.no_grad() to prevent memory leaks during inference
        with torch.no_grad():
            results = model(frame, verbose=False)
        
        detections: list[dict] = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence < self.CONFIDENCE_THRESHOLD:
                    continue

                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                if class_name not in self.TARGET_CLASSES:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x1": round(x1 / width, 4),
                        "y1": round(y1 / height, 4),
                        "x2": round(x2 / width, 4),
                        "y2": round(y2 / height, 4),
                    },
                })
        
        # Clear CUDA cache if using GPU to free memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return detections