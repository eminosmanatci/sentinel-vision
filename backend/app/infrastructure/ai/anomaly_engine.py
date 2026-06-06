"""Rule-based anomaly detection engine for security footage analysis.

Detects suspicious patterns: night intrusions, restricted zone entries,
abandoned objects, and loitering behavior. Designed to be stateless
for safe concurrent execution in Celery workers.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import logger
from app.domain.entities import AnomalyType


@dataclass(frozen=True)
class DetectionContext:
    """Immutable context for a single detection event.

    Attributes:
        timestamp: Video timestamp in seconds.
        object_class: Detected object class (e.g., "person", "car").
        bbox: Bounding box coordinates {x1, y1, x2, y2}.
        previous_detections: Optional list of prior detections for tracking.
    """
    timestamp: float
    object_class: str
    bbox: dict[str, float]
    previous_detections: list[dict] = field(default_factory=list)


class AnomalyEngine:
    """Stateless anomaly detection engine with configurable rule sets.

    All detection history is passed via DetectionContext.previous_detections
    to ensure thread-safe operation across Celery workers.
    """

    # Class-level configuration for restricted zones
    # In production, load from database or config file
    RESTRICTED_ZONES: list[dict] = []

    # Time thresholds (seconds)
    STATIONARY_THRESHOLD: float = 300.0  # 5 minutes
    LOITERING_WINDOW: float = 600.0      # 10 minutes
    LOITERING_COUNT: int = 3
    LOITERING_IOU_THRESHOLD: float = 0.3 # Lower threshold to account for slight movement

    def check_anomaly(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Evaluate all anomaly rules against a detection event.

        Rules are checked in priority order. First match wins.

        Args:
            ctx: Detection context with current and historical data.

        Returns:
            Tuple of (is_anomaly, anomaly_type).
        """
        rules = [
            self._check_night_intrusion,
            self._check_restricted_zone,
            self._check_abandoned_object,
            self._check_loitering,
        ]

        for rule in rules:
            is_anomaly, anomaly_type = rule(ctx)
            if is_anomaly:
                return True, anomaly_type

        return False, AnomalyType.NONE

    def _check_night_intrusion(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 1: Person detected during night hours (00:00-06:00)."""
        if ctx.object_class != "person":
            return False, AnomalyType.NONE

        hour = int(ctx.timestamp // 3600) % 24
        if 0 <= hour < 6:
            logger.info(
                "Night intrusion detected",
                extra={"timestamp": ctx.timestamp, "hour": hour},
            )
            return True, AnomalyType.NIGHT_INTRUSION

        return False, AnomalyType.NONE

    def _check_restricted_zone(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 2: Object enters a predefined restricted zone."""
        if not self.RESTRICTED_ZONES:
            return False, AnomalyType.NONE

        center_x = (ctx.bbox["x1"] + ctx.bbox["x2"]) / 2
        center_y = (ctx.bbox["y1"] + ctx.bbox["y2"]) / 2

        for zone in self.RESTRICTED_ZONES:
            if (
                zone["x1"] <= center_x <= zone["x2"]
                and zone["y1"] <= center_y <= zone["y2"]
            ):
                logger.info(
                    "Restricted zone entry detected",
                    extra={"timestamp": ctx.timestamp, "zone": zone},
                )
                return True, AnomalyType.RESTRICTED_ZONE

        return False, AnomalyType.NONE

    def _check_abandoned_object(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 3: Non-person object stationary for >5 minutes."""
        if ctx.object_class == "person":
            return False, AnomalyType.NONE

        iou_threshold = 0.8
        history = [
            h for h in ctx.previous_detections
            if h.get("object_class") == ctx.object_class
        ]

        for prev in history:
            if self._compute_iou(ctx.bbox, prev["bbox"]) > iou_threshold:
                elapsed = ctx.timestamp - prev["timestamp"]
                if elapsed > self.STATIONARY_THRESHOLD:
                    logger.info(
                        "Abandoned object detected",
                        extra={"timestamp": ctx.timestamp, "elapsed": elapsed},
                    )
                    return True, AnomalyType.ABANDONED_OBJECT

        return False, AnomalyType.NONE

    def _check_loitering(self, ctx: DetectionContext) -> tuple[bool, AnomalyType]:
        """Rule 4: Person staying in the same general area for 10+ minutes."""
        if ctx.object_class != "person":
            return False, AnomalyType.NONE

        history = [
            h for h in ctx.previous_detections
            if h.get("object_class") == "person"
        ]

        # Filter history for people in the SAME general location within the time window
        recent_in_area = [
            h for h in history
            if (ctx.timestamp - h["timestamp"] <= self.LOITERING_WINDOW) and 
               (self._compute_iou(ctx.bbox, h["bbox"]) > self.LOITERING_IOU_THRESHOLD)
        ]

        if len(recent_in_area) >= self.LOITERING_COUNT - 1:
            logger.info(
                "Suspicious loitering detected",
                extra={
                    "timestamp": ctx.timestamp,
                    "detection_count": len(recent_in_area) + 1,
                },
            )
            return True, AnomalyType.SUSPICIOUS_LOITERING

        return False, AnomalyType.NONE

    @staticmethod
    def _compute_iou(box1: dict, box2: dict) -> float:
        """Compute Intersection over Union (IoU) for two bounding boxes."""
        x_left = max(box1["x1"], box2["x1"])
        y_top = max(box1["y1"], box2["y1"])
        x_right = min(box1["x2"], box2["x2"])
        y_bottom = min(box1["y2"], box2["y2"])

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
        area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])

        union = area1 + area2 - intersection
        return intersection / union if union > 0 else 0.0