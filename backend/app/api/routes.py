"""API routes for SentinelVision video analytics platform.

This module defines RESTful endpoints for video upload, retrieval,
detection queries, and AI-powered chat interactions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.dependencies import get_detection_repository, get_video_service
from app.infrastructure.tasks.video_tasks import process_video_task
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.detection import DetectionListResponse, DetectionResponse
from app.schemas.video import VideoListResponse, VideoResponse, VideoUploadResponse
from app.services.rag_service import RAGService
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/v1", tags=["videos"])


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,  # 202 Accepted for async processing
    summary="Upload a security video for AI analysis",
    description=(
        "Uploads a video file and queues it for background processing. "
        "The video will be analyzed using YOLOv8 object detection, "
        "OpenAI embeddings, and anomaly detection rules."
    ),
)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload (mp4, avi, mov)"),
    video_service: VideoService = Depends(get_video_service),
) -> VideoUploadResponse:
    """Handle video upload and trigger async processing pipeline.

    Args:
        file: Uploaded video file.
        video_service: Injected video service dependency.

    Returns:
        VideoUploadResponse with upload status and processing queue info.

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors.
    """
    try:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        video_service.validate_file(file.filename or "unknown", file_size)

        # Persist video metadata
        video = await video_service.create_upload(file.filename or "unknown")

        # Write file to disk
        content = await file.read()
        with open(video.file_path, "wb") as buffer:
            buffer.write(content)

        # 🚀 Queue Celery task for background processing
        task = process_video_task.delay(str(video.id))
        logger.info(
            "Video upload successful. Celery task queued.",
            extra={
                "video_id": str(video.id),
                "task_id": task.id,
                "filename": video.filename,
                "file_size_bytes": file_size,
            },
        )

        return VideoUploadResponse(
            id=video.id,
            filename=video.filename,
            status="processing",
            message="Video uploaded and queued for processing.",
            task_id=task.id,  # Add task_id for tracking
        )

    except ValidationError as exc:
        logger.warning(f"Upload validation failed: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error(f"Upload failed unexpectedly: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(exc)}",
        )


@router.get(
    "/videos",
    response_model=VideoListResponse,
    summary="List uploaded videos with pagination",
)
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    video_service: VideoService = Depends(get_video_service),
) -> VideoListResponse:
    """Retrieve paginated list of uploaded videos.

    Args:
        limit: Maximum number of videos to return.
        offset: Pagination offset.
        video_service: Injected video service.

    Returns:
        VideoListResponse containing video items and total count.
    """
    videos = await video_service.list_videos(limit=limit, offset=offset)
    return VideoListResponse(
        items=[
            VideoResponse(
                id=v.id,
                filename=v.filename,
                duration_seconds=v.duration_seconds,
                fps=v.fps,
                resolution=v.resolution,
                status=v.status.value,
                created_at=v.created_at,
                processed_at=v.processed_at,
            )
            for v in videos
        ],
        total=len(videos),
    )


@router.get(
    "/videos/{video_id}",
    response_model=VideoResponse,
    summary="Get video details by ID",
)
async def get_video(
    video_id: str,
    video_service: VideoService = Depends(get_video_service),
) -> VideoResponse:
    """Retrieve detailed information for a specific video.

    Args:
        video_id: UUID string of the video.
        video_service: Injected video service.

    Returns:
        VideoResponse with full video metadata.

    Raises:
        HTTPException: 404 if video not found.
    """
    video = await video_service.get_video(UUID(video_id))
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    return VideoResponse(
        id=video.id,
        filename=video.filename,
        duration_seconds=video.duration_seconds,
        fps=video.fps,
        resolution=video.resolution,
        status=video.status.value,
        created_at=video.created_at,
        processed_at=video.processed_at,
    )


@router.get(
    "/videos/{video_id}/detections",
    response_model=DetectionListResponse,
    summary="Get AI detections for a video",
)
async def get_video_detections(
    video_id: str,
    detection_repo=Depends(get_detection_repository),
) -> DetectionListResponse:
    """Retrieve all object detections and anomalies for a specific video.

    Args:
        video_id: UUID string of the video.
        detection_repo: Injected detection repository.

    Returns:
        DetectionListResponse with detection items and total count.
    """
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
                anomaly_type=(
                    d.anomaly_type.value
                    if hasattr(d.anomaly_type, "value")
                    else str(d.anomaly_type)
                ),
            )
            for d in detections
        ],
        total=len(detections),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI-powered chat query over security footage",
)
async def chat(
    request: ChatRequest,
    detection_repo=Depends(get_detection_repository),
) -> ChatResponse:
    """Process natural language queries about security footage using RAG.

    Uses vector similarity search (pgvector) and GPT-4o-mini to answer
    questions about detected objects, anomalies, and events.

    Args:
        request: ChatRequest containing the query and optional video filter.
        detection_repo: Injected detection repository.

    Returns:
        ChatResponse with AI-generated answer and source references.
    """
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