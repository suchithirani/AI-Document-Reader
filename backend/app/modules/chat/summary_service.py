from app.modules.chat.repository import ChatRepository
from app.services.ai.summary_service import (
    SummaryGenerationService,
)


class ChatSummaryService:

    def __init__(
        self,
        db,
    ):

        self.repository = ChatRepository(
            db,
        )

        self.summary_service = SummaryGenerationService(db)

    async def generate_summary(
        self,
        session_id: str,
    ):

        messages = await self.repository.get_messages(
            session_id,
        )

        if len(messages) < 10:
            return

        conversation = []

        for message in messages:

            conversation.append(
                f"{message.role}: {message.content}"
            )

        summary = await self.summary_service.generate_summary(
            "\n".join(conversation),
            session_id,
        )

        await self.repository.update_summary(
            session_id,
            summary,
        )