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
from app.modules.chat.chat_session_repository import ChatSessionDocumentRepository
from app.workers.chat_tasks import generate_chat_title_task
from app.workers.chat_summary_task import generate_summary_task


class ChatService:

    def __init__(self, db):
        self.db = db
        self.repository = ChatRepository(db)
        self.search_service = SearchService(db)
        self.document_repository = DocumentRepository(db)
        self.chat_session_document_repository = ChatSessionDocumentRepository(db)

    async def create_session(
        self,
        owner_id: str,
        document_ids: list[str] | None = None,
        collection_id: str | None = None,
    ):
        if collection_id:
            from app.modules.document_collections.repository import DocumentCollectionRepository
            col_repo = DocumentCollectionRepository(self.db)
            collection = await col_repo.get_collection(collection_id)
            if collection is None:
                raise NotFoundException("Collection not found.")
            if collection.owner_id != owner_id:
                raise ForbiddenException("Access to this collection is denied.")
            document_ids = collection.document_ids

        if not document_ids:
            raise BadRequestException("No documents linked to this chat session.")

        for document_id in document_ids:
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
                    f"Document {document_id} has not been processed yet."
                )

        session = {
            "owner_id": owner_id,
            "title": "New Chat",
            "title_generated": False,
            "summary": None,
            "summary_updated_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }

        created_session = await self.repository.create_session(
            session
        )

        await self.chat_session_document_repository.add_documents(
            session_id=str(created_session.id),
            document_ids=document_ids,
        )
        return created_session

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
        detail_level: str = "standard",
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

        document_ids = (
            await self.chat_session_document_repository.get_document_ids(
                session_id,
            )
        )
        print("DOCUMENT IDS:", document_ids)

        for document_id in document_ids:

            document = (
                await self.document_repository.get_document_by_id(
                    document_id,
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
                    f"{document.original_filename} has not been processed yet."
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
            limit=4,
        )

        result = await self.search_service.search(
            owner_id=owner_id,
            session_id=session_id,
            document_ids=document_ids,
            question=question,
            history=history,
            summary=session.summary,
            detail_level=detail_level,
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
        messages = await self.repository.get_messages(
            session_id,
        )
        if len(messages) % 10 ==0:
            generate_summary_task.delay(
                session_id=session_id,
            )
        if not session.title_generated:

            await self.repository.mark_title_generated(
                session_id,
            )

            generate_chat_title_task.delay(
                session_id=session_id,
                question=question,
                answer=result["answer"],
            )

        if len(messages) == 1 or len(messages) % 5 == 0:
            from app.workers.ai_tasks import update_user_memory_task
            update_user_memory_task.delay(
                owner_id=owner_id,
                session_id=session_id,
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
    async def send_message_stream(
        self,
        owner_id: str,
        session_id: str,
        question: str,
        detail_level: str = "standard",
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

        document_ids = (
            await self.chat_session_document_repository.get_document_ids(
                session_id,
            )
        )
        print("DOCUMENT IDS:", document_ids)

        for document_id in document_ids:

            document = (
                await self.document_repository.get_document_by_id(
                    document_id,
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
                    f"{document.original_filename} has not been processed yet."
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
            limit=4,
        )

        import json
        sources = None
        async for chunk in self.search_service.search_stream(
            owner_id=owner_id,
            session_id=session_id,
            document_ids=document_ids,
            question=question,
            history=history,
            summary=session.summary,
            detail_level=detail_level,
        ):
            if chunk["type"] == "chunk":
                yield chunk
            elif chunk["type"] == "sources":
                sources = chunk["content"]
                yield chunk
            elif chunk["type"] == "done":
                answer = chunk["content"]
                await self.repository.create_message(
                    {
                        "session_id": session_id,
                        "role": ChatRole.ASSISTANT,
                        "content": answer,
                        "sources": sources,
                        "created_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC),
                    }
                )
                messages = await self.repository.get_messages(session_id)
                if len(messages) % 10 == 0:
                    generate_summary_task.delay(session_id=session_id)
                
                if not session.title_generated:
                    await self.repository.mark_title_generated(session_id)
                    generate_chat_title_task.delay(
                        session_id=session_id,
                        question=question,
                        answer=answer,
                    )
                
                if len(messages) == 1 or len(messages) % 5 == 0:
                    from app.workers.ai_tasks import update_user_memory_task
                    update_user_memory_task.delay(
                        owner_id=owner_id,
                        session_id=session_id,
                    )

