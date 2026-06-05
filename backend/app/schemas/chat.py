from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    video_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float


class DetectionQueryResponse(BaseModel):
    id: str
    timestamp: float
    object_class: str
    confidence: float
    description: str
    is_anomaly: bool
    anomaly_type: str
    similarity: float | None = None