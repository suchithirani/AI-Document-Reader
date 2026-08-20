from app.common.constants import CollectionName
from app.common.utils.datetime import utc_now
from app.modules.chat.model import (
    ChatMessage,
    ChatSession,
)
from app.repositories.base_repository import (
    BaseRepository,
)


class ChatRepository(BaseRepository):

    def __init__(self, db):

        super().__init__(
            db[
                CollectionName.CHAT_SESSIONS.value
            ]
        )

        self.message_collection = db[
            CollectionName.CHAT_MESSAGES.value
        ]


    async def create_session(
        self,
        session: dict,
    ) -> ChatSession:

        created = await self.create(session)

        return ChatSession.model_validate(
            created
        )

    async def get_session(
        self,
        session_id: str,
    ) -> ChatSession | None:

        session = await super().get_by_id(
            session_id
        )

        if session is None:
            return None

        return ChatSession.model_validate(
            session
        )

    async def get_sessions(
        self,
        owner_id: str,
    ) -> list[ChatSession]:

        sessions = await self.get_many(
            filters={
                "owner_id": owner_id,
                "deleted_at": None,
            },
            sort=[
                ("updated_at", -1),
            ],
        )

        return [
            ChatSession.model_validate(
                session
            )
            for session in sessions
        ]

    async def update_session_title(
        self,
        session_id: str,
        title: str,
    ) -> ChatSession | None:

        session = await self.update(
            session_id,
            {
                "title": title,
                "updated_at": utc_now(),
            },
        )

        if session is None:
            return None

        return ChatSession.model_validate(
            session
        )

    async def delete_session(
        self,
        session_id: str,
    ) -> ChatSession | None:

        session = await self.update(
            session_id,
            {
                "deleted_at": utc_now(),
                "updated_at": utc_now(),
            },
        )

        if session is None:
            return None

        return ChatSession.model_validate(
            session
        )

    async def create_message(
        self,
        message: dict,
    ) -> ChatMessage:

        result = await self.message_collection.insert_one(
            message
        )

        message["_id"] = str(
            result.inserted_id
        )

        return ChatMessage.model_validate(
            message
        )

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[ChatMessage]:

        cursor = (
            self.message_collection.find(
                {
                    "session_id": session_id,
                }
            )
            .sort(
                "created_at",
                -1,
            )
            .limit(limit)
        )

        messages = await cursor.to_list(
            length=limit,
        )

        messages.reverse()

        return [
            ChatMessage.model_validate(
                self._serialize_document(message),
            )
            for message in messages
        ]

    async def get_messages(
        self,
        session_id: str,
    ) -> list[ChatMessage]:

        cursor = (
            self.message_collection.find(
                {
                    "session_id": session_id,
                }
            )
            .sort(
                "created_at",
                1,
            )
        )

        messages = await cursor.to_list(
            length=None
        )

        return [
            ChatMessage.model_validate(
                self._serialize_document(message),
            )
            for message in messages
        ]

    async def mark_title_generated(
        self,
        session_id: str,
    ):

        await self.update(
            session_id,
            {
                "title_generated": True,
                "updated_at": utc_now(),
            },
        )

    async def update_summary(
        self,
        session_id: str,
        summary: str,
    ):

        session = await self.update(
            session_id,
            {
                "summary": summary,
                "summary_updated_at": utc_now(),
                "updated_at": utc_now(),
            },
        )

        if session is None:
            return None

        return ChatSession.model_validate(
            session,
        )