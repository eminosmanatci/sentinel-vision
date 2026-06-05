import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import logger


class OpenAIService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._embedding_model = "text-embedding-3-small"
        self._llm_model = "gpt-4o-mini"

    async def create_embedding(self, text: str) -> list[float]:
        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    async def generate_description(
        self, timestamp: float, objects: list[dict], context: str = ""
    ) -> str:
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
            return response.choices[0].message.content or "No description generated."
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return f"Objects detected at {timestamp:.1f}s: {object_str}"

    async def answer_query(self, query: str, context: list[str]) -> str:
        context_str = "\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(context)])

        prompt = (
            "You are a security analyst assistant. Answer the user's question "
            "based ONLY on the provided security camera records below.\n\n"
            f"RECORDS:\n{context_str}\n\n"
            f"QUESTION: {query}\n\n"
            "Answer based only on the records. If insufficient data, say 'Insufficient records found'."
        )

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
        return response.choices[0].message.content or "No answer generated."