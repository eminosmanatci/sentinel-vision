from uuid import UUID

from fastapi.responses import FileResponse

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


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    video_service: VideoService = Depends(get_video_service),
) -> VideoUploadResponse:
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        video_service.validate_file(file.filename or "unknown", file_size)

        video = await video_service.create_upload(file.filename or "unknown")

        content = await file.read()
        with open(video.file_path, "wb") as f:
            f.write(content)

        process_video_task.delay(str(video.id))
        logger.info(f"Background task queued for video: {video.id}")

        return VideoUploadResponse(
            id=video.id,
            filename=video.filename,
            status=video.status.value,
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/videos", response_model=VideoListResponse)
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    video_service: VideoService = Depends(get_video_service),
) -> VideoListResponse:
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


@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    video_service: VideoService = Depends(get_video_service),
) -> VideoResponse:
    video = await video_service.get_video(UUID(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

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

@router.get("/videos/{video_id}/detections", response_model=DetectionListResponse)
async def get_video_detections(
    video_id: str,
    detection_repo=Depends(get_detection_repository),
) -> DetectionListResponse:
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
                anomaly_type=d.anomaly_type.value if d.anomaly_type else "",
            )
            for d in detections
        ],
        total=len(detections),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    detection_repo=Depends(get_detection_repository),
) -> ChatResponse:
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

@router.get("/uploads/{video_id}/video.mp4")
async def serve_video(video_id: str):
    from app.core.config import settings
    from pathlib import Path

    file_path = Path(settings.UPLOAD_DIR) / video_id / "video.mp4"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(str(file_path), media_type="video/mp4")