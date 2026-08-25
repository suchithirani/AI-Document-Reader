import re

from google import genai

from app.core.config import settings


class GeminiRerankerService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def rerank(
        self,
        question: str,
        results: list,
        top_k: int = 5,
    ):

        if not results:

            return []

        prompt = f"""
You are an AI reranker.

Rank the document chunks by relevance.

Return ONLY comma-separated chunk numbers.

Example:
2,5,1,4,3

Do not explain.
Do not use markdown.

Question:
{question}

Chunks:
"""

        for index, result in enumerate(
            results,
            start=1,
        ):

            prompt += (
                f"\nChunk {index}\n"
                f"{result['chunk'].text}\n"
            )

        try:

            response = self.client.models.generate_content(
                model=settings.GENERATION_MODEL,
                contents=prompt,
            )

            if not response.text:

                return results[:top_k]

            output = response.text.strip()

            indexes = [
                int(value) - 1
                for value in re.findall(
                    r"\d+",
                    output,
                )
            ]

            reranked = []

            for index in indexes:

                if 0 <= index < len(results):

                    reranked.append(
                        results[index]
                    )

            if reranked:

                return reranked[:top_k]

        except Exception:

            pass

        return results[:top_k]
