"""OpenAI service with fallback for development/testing."""

import httpx
from openai import AsyncOpenAI, APIError, RateLimitError

from app.core.config import settings
from app.core.logging import logger


class OpenAIService:
    """OpenAI API service with graceful fallback for quota/billing issues."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._embedding_model = "text-embedding-3-small"
        self._llm_model = "gpt-4o-mini"
        self._fallback_mode = False

    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding with fallback to zero-vector on API failure."""
        if self._fallback_mode or not settings.OPENAI_API_KEY:
            return self._dummy_embedding()

        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding

        except (RateLimitError, APIError) as exc:
            logger.warning(f"OpenAI embedding failed, using fallback: {exc}")
            self._fallback_mode = True
            return self._dummy_embedding()

    async def generate_description(
        self, timestamp: float, objects: list[dict], context: str = ""
    ) -> str:
        """Generate description with fallback on API failure."""
        if self._fallback_mode or not settings.OPENAI_API_KEY:
            return self._dummy_description(timestamp, objects)

        object_str = ", ".join([
            f"{obj['class_name']} ({obj['confidence']:.0%})"
            for obj in objects
        ])

        prompt = (
            f"Timestamp: {timestamp:.1f}s. Detected objects: {object_str}. "
            f"Context: {context}. "
            "Generate a concise security observation in English."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security camera AI analyst. Generate brief, factual observations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.3,
            )
            return response.choices[0].message.content or self._dummy_description(timestamp, objects)

        except (RateLimitError, APIError) as exc:
            logger.warning(f"OpenAI description failed, using fallback: {exc}")
            self._fallback_mode = True
            return self._dummy_description(timestamp, objects)

    async def answer_query(self, query: str, context: list[str]) -> str:
        """Answer query with fallback on API failure."""
        if self._fallback_mode or not settings.OPENAI_API_KEY:
            return self._dummy_answer(query, context)

        context_str = "\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(context)])

        prompt = (
            "You are a security analyst assistant. Answer the user's question "
            "based ONLY on the provided security camera records below.\n\n"
            f"RECORDS:\n{context_str}\n\n"
            f"QUESTION: {query}\n\n"
            "Answer based only on the records. If insufficient data, say 'Insufficient records found'."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze security footage records and answer factual questions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.2,
            )
            return response.choices[0].message.content or self._dummy_answer(query, context)

        except (RateLimitError, APIError) as exc:
            logger.warning(f"OpenAI query failed, using fallback: {exc}")
            self._fallback_mode = True
            return self._dummy_answer(query, context)

    @staticmethod
    def _dummy_embedding() -> list[float]:
        """Return zero-vector placeholder embedding."""
        return [0.0] * 1536

    @staticmethod
    def _dummy_description(timestamp: float, objects: list[dict]) -> str:
        """Generate local description without OpenAI."""
        if not objects:
            return f"No objects detected at {timestamp:.1f}s."
        
        obj_list = ", ".join([
            f"{obj['class_name']} ({obj['confidence']:.0%})"
            for obj in objects
        ])
        return f"At {timestamp:.1f}s: {obj_list} detected."

    @staticmethod
    def _dummy_answer(query: str, context: list[str]) -> str:
        """Generate local answer without OpenAI."""
        if not context:
            return "Insufficient records found for this query."
        
        return (
            f"Based on {len(context)} records: "
            f"Query '{query}' refers to security footage analysis. "
            "Please upgrade to a paid OpenAI plan for detailed AI responses."
        )