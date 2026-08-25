from app.modules.chat.repository import ChatRepository
from app.services.ai.title_service import TitleGenerationService


class ChatTitleService:

    def __init__(
        self,
        db,
    ):

        self.repository = ChatRepository(
            db,
        )

        self.title_service = (
            TitleGenerationService(db)
        )

    async def generate_title(
        self,
        session_id: str,
        question: str,
        answer: str,
    ):

        session = await self.repository.get_session(
            session_id,
        )

        if session is None:
            return

        if session.title != "New Chat":
            return

        title = await self.title_service.generate_title(
            session_id,
            question,
            answer,
        )

        await self.repository.update_session_title(
            session_id,
            title,
        )
