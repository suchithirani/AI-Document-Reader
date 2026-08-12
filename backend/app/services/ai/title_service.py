from app.core.config import settings
from app.services.ai.service import AIService
from app.services.analytics.ai_usage import AIUsageService



class TitleGenerationService:

    def __init__(self,db):

        self.ai_service = AIService()
        self.ai_usage = AIUsageService(db)  

    async def generate_title(
        self,
        session_id: str,
        question: str,
        answer: str,
    ) -> str:

        prompt = f"""
You are generating the title of an AI document conversation.

Conversation:

User Question:
{question}

Assistant Response:
{answer}

Instructions:

- Produce exactly one title.
- Maximum 5 words.
- Use Title Case.
- Do not use quotation marks.
- Do not use punctuation.
- Be specific to the conversation topic.
- Prefer important nouns over generic words.
- Do not use words such as:
  File, Files, Document, Documents,
  Information, Data, Content,
  Uploaded, Shared, Related,
  Conversation, Chat, Assistant.
- If multiple documents are discussed, generate a title describing the overall topic rather than mentioning files.
- Return ONLY the title.
"""

        response = await self.ai_service.answer_question(
            prompt,
        )
        title = response["answer"]

        await self.ai_usage.log(
            user_id=None,
            session_id=session_id,
            document_id=None,
            endpoint="title_generation",
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
            latency_ms=response["latency_ms"],
        )
        return title