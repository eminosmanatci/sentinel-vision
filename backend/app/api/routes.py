"""API routes for SentinelVision video analytics platform."""

from datetime import datetime, timezone
from uuid import UUID
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.dependencies import get_detection_repository, get_video_service
from app.infrastructure.tasks.celery_app import celery_app
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.detection import DetectionListResponse, DetectionResponse
from app.schemas.video import VideoListResponse, VideoResponse, VideoUploadResponse
from app.services.rag_service import RAGService
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/v1", tags=["videos"])

CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming large files


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a security video for AI analysis",
)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload (mp4, avi, mov)"),
    video_service: VideoService = Depends(get_video_service),
) -> VideoUploadResponse:
    """Handle video upload and trigger async processing pipeline."""
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        filename = file.filename or "unknown.mp4"
        video_service.validate_file(filename, file_size)

        video = await video_service.create_upload(filename)

        with open(video.file_path, "wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE):
                buffer.write(chunk)

        task = celery_app.send_task(
            "app.infrastructure.tasks.video_tasks.process_video_task",
            args=[str(video.id)],
        )
        
        logger.info(
            "Celery task queued successfully",
            extra={"video_id": str(video.id), "task_id": task.id, "video_name": video.filename},
        )

        return VideoUploadResponse(
            id=video.id,
            filename=video.filename,
            status="processing",
            message="Video uploaded and queued for processing.",
            task_id=task.id,
        )

    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Upload failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}")


@router.get("/videos", response_model=VideoListResponse)
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    video_service: VideoService = Depends(get_video_service),
) -> VideoListResponse:
    """Retrieve paginated list of uploaded videos."""
    videos = await video_service.list_videos(limit=limit, offset=offset)
    return VideoListResponse(
        items=[
            VideoResponse(
                id=v.id,
                filename=v.filename,
                duration_seconds=v.duration_seconds,
                fps=v.fps,
                resolution=v.resolution,
                status=v.status.value if hasattr(v.status, 'value') else str(v.status),
                created_at=v.created_at or datetime.now(timezone.utc),
                processed_at=v.processed_at,
            )
            for v in videos
        ],
        total=len(videos),
    )


@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    video_service: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Retrieve detailed information for a specific video."""
    video = await video_service.get_video(UUID(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoResponse(
        id=video.id,
        filename=video.filename,
        duration_seconds=video.duration_seconds,
        fps=video.fps,
        resolution=video.resolution,
        status=video.status.value if hasattr(video.status, 'value') else str(video.status),
        created_at=video.created_at or datetime.now(timezone.utc),
        processed_at=video.processed_at,
    )


@router.get("/videos/{video_id}/detections", response_model=DetectionListResponse)
async def get_video_detections(
    video_id: str,
    detection_repo: Any = Depends(get_detection_repository),
) -> DetectionListResponse:
    """Retrieve all object detections and anomalies for a specific video."""
    detections = await detection_repo.get_by_video_id(UUID(video_id))
    return DetectionListResponse(
        items=[
            DetectionResponse(
                id=str(d.id),
                timestamp=d.timestamp,
                frame_number=d.frame_number,
                object_class=d.object_class,
                confidence=d.confidence,
                description=d.description,
                is_anomaly=d.is_anomaly,
                anomaly_type=d.anomaly_type.value if hasattr(d.anomaly_type, "value") else str(d.anomaly_type),
            )
            for d in detections
        ],
        total=len(detections),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    detection_repo: Any = Depends(get_detection_repository),
) -> ChatResponse:
    """Process natural language queries about security footage using RAG."""
    try:
        video_id = UUID(request.video_id) if request.video_id else None
    except ValueError:
        video_id = None

    rag = RAGService(detection_repo)
    result = await rag.answer(request.query, video_id)

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
    )