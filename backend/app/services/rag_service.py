"""RAG (Retrieval-Augmented Generation) service for video querying."""

from uuid import UUID

from app.core.logging import logger
from app.infrastructure.ai.openai_service import OpenAIService
from app.repositories.base import DetectionRepository


class RAGService:
    """Service to handle natural language queries over video detections."""

    def __init__(
        self,
        detection_repo: DetectionRepository,
        openai_service: OpenAIService | None = None,
    ) -> None:
        self._detection_repo = detection_repo
        self._openai = openai_service or OpenAIService()

    async def answer(self, query: str, video_id: UUID | None = None) -> dict:
        """Process a natural language query and return an AI-generated answer.
        
        Args:
            query: The user's natural language question.
            video_id: Optional UUID to restrict the search to a specific video (Pre-filtering).
            
        Returns:
            Dictionary containing the answer, source records, and confidence score.
        """
        logger.info(
            "Executing RAG pipeline",
            extra={"query": query, "target_video_id": str(video_id) if video_id else "ALL"},
        )

        # 1. Create embedding from the text query
        query_embedding = await self._openai.create_embedding(query)

        # 2. Search similar detections (Database-level Pre-filtering applied)
        # CRITICAL: video_id must be passed to the DB query to ensure we get 
        # the top 5 matches specifically for this video, avoiding empty contexts.
        similar_detections = await self._detection_repo.search_similar(
            query_embedding=query_embedding,
            limit=5,
            video_id=video_id,
        )

        # 3. Build context and source metadata
        context: list[str] = []
        sources: list[dict] = []

        for det in similar_detections:
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
                "anomaly_type": det.anomaly_type.value if getattr(det, "anomaly_type", None) else None,
            })

        if not context:
            logger.info("No relevant records found in vector database.")
            return {
                "answer": "No relevant records found for this query in the specified video(s).",
                "sources": [],
                "confidence": 0.0,
            }

        # 4. Generate natural language answer using LLM
        answer = await self._openai.answer_query(query, context)

        # Simple confidence estimation based on retrieved source count
        confidence = min(len(sources) / 5.0, 1.0)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 2),
        }