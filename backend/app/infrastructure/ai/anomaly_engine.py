from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import logger
from app.domain.entities import AnomalyType


@dataclass
class DetectionContext:
    timestamp: float
    object_class: str
    bbox: dict[str, float]
    previous_detections: list[dict] = field(default_factory=list)


class AnomalyEngine:
    def __init__(self) -> None:
        self._object_history: dict[str, list[dict]] = {}
        self._restricted_zones: list[dict] = []

    def check_anomaly(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        checks = [
            self._check_night_intrusion,
            self._check_restricted_zone,
            self._check_abandoned_object,
            self._check_loitering,
        ]

        for check in checks:
            is_anomaly, anomaly_type = check(ctx)
            if is_anomaly:
                return True, anomaly_type

        self._update_history(ctx)
        return False, AnomalyType.NONE

    def _check_night_intrusion(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 1: Person detected during night hours (00:00-06:00)"""
        if ctx.object_class != "person":
            return False, AnomalyType.NONE

        hour = int(ctx.timestamp // 3600) % 24
        # For demo: assume timestamp is seconds from midnight of recording day
        # In production, use actual datetime from video metadata
        if 0 <= hour < 6:
            logger.info(f"Night intrusion detected at {ctx.timestamp}s")
            return True, AnomalyType.NIGHT_INTRUSION

        return False, AnomalyType.NONE

    def _check_restricted_zone(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 2: Object enters predefined restricted zone"""
        if not self._restricted_zones:
            return False, AnomalyType.NONE

        cx = (ctx.bbox["x1"] + ctx.bbox["x2"]) / 2
        cy = (ctx.bbox["y1"] + ctx.bbox["y2"]) / 2

        for zone in self._restricted_zones:
            if (zone["x1"] <= cx <= zone["x2"] and zone["y1"] <= cy <= zone["y2"]):
                logger.info(f"Restricted zone entry at {ctx.timestamp}s")
                return True, AnomalyType.RESTRICTED_ZONE

        return False, AnomalyType.NONE

    def _check_abandoned_object(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 3: Object stationary for >5 minutes"""
        stationary_threshold = 300  # 5 minutes in seconds
        iou_threshold = 0.8

        if ctx.object_class in ["person"]:
            return False, AnomalyType.NONE

        key = f"{ctx.object_class}"
        history = self._object_history.get(key, [])

        for prev in history:
            if self._iou(ctx.bbox, prev["bbox"]) > iou_threshold:
                elapsed = ctx.timestamp - prev["timestamp"]
                if elapsed > stationary_threshold:
                    logger.info(f"Abandoned object detected at {ctx.timestamp}s")
                    return True, AnomalyType.ABANDONED_OBJECT

        return False, AnomalyType.NONE

    def _check_loitering(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 4: Same person detected 3+ times in 10 minutes"""
        if ctx.object_class != "person":
            return False, AnomalyType.NONE

        window = 600  # 10 minutes
        count_threshold = 3

        key = "person"
        history = self._object_history.get(key, [])

        recent = [
            h for h in history
            if ctx.timestamp - h["timestamp"] <= window
        ]

        if len(recent) >= count_threshold - 1:
            logger.info(f"Suspicious loitering detected at {ctx.timestamp}s")
            return True, AnomalyType.SUSPICIOUS_LOITERING

        return False, AnomalyType.NONE

    def _update_history(self, ctx: DetectionContext) -> None:
        key = ctx.object_class
        if key not in self._object_history:
            self._object_history[key] = []

        self._object_history[key].append({
            "timestamp": ctx.timestamp,
            "bbox": ctx.bbox,
        })

        # Keep last 100 entries per class
        self._object_history[key] = self._object_history[key][-100:]

    @staticmethod
    def _iou(box1: dict, box2: dict) -> float:
        xi1 = max(box1["x1"], box2["x1"])
        yi1 = max(box1["y1"], box2["y1"])
        xi2 = min(box1["x2"], box2["x2"])
        yi2 = min(box2["y2"], box2["y2"])

        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
        box2_area = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])

        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0