"""Celery tasks package for SentinelVision.

This module registers Celery tasks. Import order is critical:
- celery_app.py defines the Celery app instance (no task imports)
- video_tasks.py imports celery_app and defines tasks (no circular import)
"""

from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.tasks.video_tasks import process_video_task

__all__ = ["celery_app", "process_video_task"]