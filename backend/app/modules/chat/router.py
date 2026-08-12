from fastapi import APIRouter, Depends

from app.common.response import success_response
from app.dependencies.auth import get_current_user
from app.dependencies.service import get_chat_service
from app.modules.auth.model import User
from app.modules.chat.schema import (
    CreateChatSessionRequest,
    SendMessageRequest,
    UpdateChatSessionRequest,
)
from app.modules.chat.service import ChatService
from app.dependencies.rate_limit import rate_limit


chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@chat_router.post("/sessions",dependencies=[rate_limit(limit=20, window=60)],)
async def create_session(
    body: CreateChatSessionRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    result = await service.create_session(
        owner_id=current_user.id,
        document_ids=body.document_ids,
    )

    return success_response(
        message="Chat session created successfully.",
        data=result,
    )


@chat_router.get("/sessions",dependencies=[rate_limit(limit=60, window=60)],)
async def get_sessions(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    result = await service.get_sessions(
        current_user.id,
    )

    return success_response(
        message="Chat sessions fetched successfully.",
        data=result,
    )


@chat_router.patch("/sessions/{session_id}",dependencies=[rate_limit(limit=30, window=60)],)
async def rename_session(
    session_id: str,
    body: UpdateChatSessionRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    result = await service.rename_session(
        owner_id=current_user.id,
        session_id=session_id,
        title=body.title,
    )

    return success_response(
        message="Chat session updated successfully.",
        data=result,
    )


@chat_router.delete("/sessions/{session_id}",dependencies=[rate_limit(limit=30, window=60)],)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    await service.delete_session(
        owner_id=current_user.id,
        session_id=session_id,
    )

    return success_response(
        message="Chat session deleted successfully.",
    )


@chat_router.post("/sessions/{session_id}/messages",dependencies=[rate_limit(limit=30, window=60)],)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    result = await service.send_message(
        owner_id=current_user.id,
        session_id=session_id,
        question=body.question,
    )
    
    return success_response(
        message="Message sent successfully.",
        data=result,
    )


@chat_router.get("/sessions/{session_id}/messages",dependencies=[rate_limit(limit=30, window=60)],)
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):

    result = await service.get_history(
        owner_id=current_user.id,
        session_id=session_id,
    )

    return success_response(
        message="Chat history fetched successfully.",
        data=result,
    )