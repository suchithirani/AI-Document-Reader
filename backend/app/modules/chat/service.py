from datetime import UTC, datetime
from unittest import result

from app.common.constants import ChatRole
from app.modules.chat.repository import (
    ChatRepository,
)
from app.modules.search.service import (
    SearchService,
)
from app.modules.documents.repository import (
    DocumentRepository,
)

from app.common.exceptions.document import (
    DocumentNotFoundException,
)

from app.common.exceptions.auth import (
    ForbiddenException,
    BadRequestException,
    NotFoundException,
)

from app.common.constants import (
    DocumentStatus,
)


class ChatService:

    def __init__(self, db):

        self.repository = ChatRepository(db)

        self.search_service = SearchService(db)

        self.document_repository = DocumentRepository(db)

    async def create_session(
        self,
        owner_id: str,
        document_id: str,
    ):

        document = (
            await self.document_repository.get_document_by_id(
                document_id
            )
        )

        if document is None:

            raise DocumentNotFoundException()

        if document.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to access this document."
            )

        if document.status != DocumentStatus.READY:

            raise BadRequestException(
                "Document has not been processed yet."
            )

        session = {
            "owner_id": owner_id,
            "document_id": document_id,
            "title": "New Chat",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }

        return await self.repository.create_session(
            session
        )

    async def get_sessions(
        self,
        owner_id: str,
    ):

        return await self.repository.get_sessions(
            owner_id
        )

    async def rename_session(
        self,
        owner_id: str,
        session_id: str,
        title: str,
    ):

        session = await self.repository.get_session(
            session_id
        )

        if session is None:

            raise NotFoundException(
                "Chat session not found."
            )

        if session.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to rename this chat."
            )

        return await self.repository.update_session_title(
            session_id,
            title,
        )

    async def delete_session(
        self,
        owner_id: str,
        session_id: str,
    ):

        session = await self.repository.get_session(
            session_id
        )

        if session is None:

            raise NotFoundException(
                "Chat session not found."
            )

        if session.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to delete this chat."
            )

        return await self.repository.delete_session(
            session_id
        )

    async def send_message(
        self,
        owner_id: str,
        session_id: str,
        question: str,
    ):

        session = await self.repository.get_session(
            session_id
        )

        if session is None:

            raise NotFoundException(
                "Chat session not found."
            )

        if session.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to access this chat."
            )

        document = (
            await self.document_repository.get_document_by_id(
                session.document_id
            )
        )

        if document is None:

            raise DocumentNotFoundException()

        if document.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to access this document."
            )

        if document.status != DocumentStatus.READY:

            raise BadRequestException(
                "Document has not been processed yet."
            )

        await self.repository.create_message(
            {
                "session_id": session_id,
                "role": ChatRole.USER,
                "content": question,
                "sources": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

        history = await self.repository.get_recent_messages(
            session_id=session_id,
        )

        result = await self.search_service.search(
            document_id=session.document_id,
            question=question,
            history=history,
        )

        await self.repository.create_message(
            {
                "session_id": session_id,
                "role": ChatRole.ASSISTANT,
                "content": result["answer"],
                "sources": result["sources"],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

        return result

    async def get_history(
        self,
        owner_id: str,
        session_id: str,
    ):

        session = await self.repository.get_session(
            session_id
        )

        if session is None:

            raise NotFoundException(
                "Chat session not found."
            )

        if session.owner_id != owner_id:

            raise ForbiddenException(
                "You are not allowed to access this chat."
            )

        return await self.repository.get_messages(
            session_id
        )