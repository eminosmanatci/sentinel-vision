#!/bin/bash
set -e

chown -R appuser:appgroup /app/uploads

echo "Running migrations..."
alembic upgrade head

case "$SERVICE_MODE" in
    "worker")
        echo "Starting Celery worker..."
        exec gosu appuser celery -A app.infrastructure.tasks.celery_app:celery_app worker --loglevel=info
        ;;
    "beat")
        echo "Starting Celery beat scheduler..."
        exec gosu appuser celery -A app.infrastructure.tasks.celery_app:celery_app beat --loglevel=info
        ;;
    *)
        echo "Starting FastAPI server..."
        exec gosu appuser uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
esac