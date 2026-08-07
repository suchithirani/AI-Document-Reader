from google import genai

from app.core.config import settings


class QueryRewriterService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    async def rewrite(
        self,
        question: str,
        history: list | None = None,
    ) -> str:

        conversation = ""

        if history:

            for message in history[-4:]:

                conversation += (
                    f"{message.role}: "
                    f"{message.content}\n"
                )

        prompt = f"""
You are a query rewriting assistant.

Rewrite the user's latest question so it is optimal for semantic document retrieval.

Rules:
- Preserve the original meaning.
- Use previous conversation only when necessary.
- Resolve vague references like:
  it, this, that, they, phase 2, project 1.
- Return ONLY the rewritten question.
- Never answer the question.

Conversation:
{conversation}

Latest Question:
{question}
"""

        try:

            response = self.client.models.generate_content(
                model=settings.GENERATION_MODEL,
                contents=prompt,
            )

            if response.text:

                return response.text.strip()

        except Exception:

            pass

        return question