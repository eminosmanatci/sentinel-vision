from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.exceptions import SentinelException, ValidationError
from app.core.logging import logger
from app.dependencies import get_processing_service, get_video_service
from app.infrastructure.tasks.video_tasks import process_video_task
from app.schemas.video import VideoListResponse, VideoResponse, VideoUploadResponse
from app.services.processing_service import ProcessingService
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

        # Trigger background processing
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
    from uuid import UUID

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
        processed_at=VideoListResponse.processed_at,
    )