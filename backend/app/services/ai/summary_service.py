from app.services.ai.service import AIService
from app.services.analytics.ai_usage import AIUsageService


class SummaryGenerationService:

    def __init__(self,db):

        self.ai_service = AIService()
        self.ai_usage = AIUsageService(db)

    async def generate_summary(
        self,
        conversation: str,
        session_id: str,
    ) -> str:

        prompt = f"""
Summarize this conversation.

Rules:
- Maximum 200 words.
- Keep important facts.
- Keep user preferences.
- Keep uploaded document topics.
- Keep unresolved questions.
- Ignore greetings.
- Return ONLY the summary.

Conversation:

{conversation}
"""

        response = await self.ai_service.answer_question(
            prompt,
        )
        summary = response["answer"]  
        await self.ai_usage.log(
            user_id=None,
            session_id=session_id,
            document_id=None,
            endpoint="summary_generation",
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
            latency_ms=response["latency_ms"],
        )
        return summary