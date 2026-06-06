"""Celery application configuration for SentinelVision."""

import os

from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings
from app.core.logging import logger

# =============================================================================
# Configuration
# =============================================================================

redis_url = settings.REDIS_URL or os.getenv("REDIS_URL", "redis://redis:6379/0")

if not redis_url:
    raise ValueError("REDIS_URL environment variable is required")

logger.info("Initializing Celery application", extra={"broker_url": redis_url})

# =============================================================================
# App Instance
# =============================================================================

celery_app = Celery("sentinel_vision")

celery_app.conf.broker_url = redis_url
celery_app.conf.result_backend = redis_url
celery_app.conf.broker_transport = "redis"

celery_app.config_from_object({
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 3600,
    "worker_prefetch_multiplier": 1,
    "broker_connection_retry_on_startup": True,
    "broker_connection_max_retries": 10,
    "result_expires": 3600,
    "task_always_eager": False,
    "worker_hijack_root_logger": False,
})

# =============================================================================
# Task Registration
# =============================================================================

# CRITICAL: Import tasks module AFTER celery_app is fully created
# This registers process_video_task with the Celery app instance
import app.infrastructure.tasks.video_tasks  # noqa: E402,F401

logger.info(
    "Celery application initialized",
    extra={
        "broker": redis_url,
        "registered_tasks": [
            name for name in celery_app.tasks.keys()
            if not name.startswith("celery.")
        ],
    },
)


@worker_ready.connect
def on_worker_ready(**kwargs) -> None:
    """Signal handler for worker startup confirmation."""
    logger.info("Celery worker ready for task processing")