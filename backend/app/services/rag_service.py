from uuid import UUID

from app.core.logging import logger
from app.infrastructure.ai.openai_service import OpenAIService
from app.repositories.base import DetectionRepository


class RAGService:
    def __init__(
        self,
        detection_repo: DetectionRepository,
        openai_service: OpenAIService | None = None,
    ) -> None:
        self._detection_repo = detection_repo
        self._openai = openai_service or OpenAIService()

    async def answer(self, query: str, video_id: UUID | None = None) -> dict:
        logger.info(f"RAG query: '{query}' | video_id: {video_id}")

        # 1. Create embedding from query
        query_embedding = await self._openai.create_embedding(query)

        # 2. Search similar detections
        similar_detections = await self._detection_repo.search_similar(
            query_embedding=query_embedding,
            limit=5,
        )

        # 3. Build context
        context = []
        sources = []

        for det in similar_detections:
            # Filter by video_id if provided
            if video_id and det.video_id != video_id:
                continue

            ctx_line = (
                f"Timestamp {det.timestamp:.1f}s: {det.description} "
                f"(Object: {det.object_class}, Confidence: {det.confidence:.0%})"
            )
            context.append(ctx_line)

            sources.append({
                "id": str(det.id),
                "timestamp": det.timestamp,
                "object_class": det.object_class,
                "description": det.description,
                "is_anomaly": det.is_anomaly,
                "anomaly_type": det.anomaly_type.value if det.anomaly_type else None,
            })

        if not context:
            return {
                "answer": "No relevant records found for this query.",
                "sources": [],
                "confidence": 0.0,
            }

        # 4. Generate answer with LLM
        answer = await self._openai.answer_query(query, context)

        # Simple confidence based on number of sources
        confidence = min(len(sources) / 5.0, 1.0)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 2),
        }