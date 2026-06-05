import os
from pathlib import Path
from typing import Generator

import cv2
import numpy as np
import torch
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
            # Fix PyTorch 2.6 weights_only issue
            torch.serialization.add_safe_globals([
                type(None),
            ])
            self._model = YOLO(self._model_name)
        return self._model
    # ... rest same