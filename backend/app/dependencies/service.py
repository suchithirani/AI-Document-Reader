from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.core.database import get_database
from app.modules.documents.service import DocumentService
from app.modules.auth.service import AuthService
from app.modules.document_contents.service import (
    DocumentContentService,
)
from app.ocr.service import OCRService
from app.modules.search.service import SearchService
from app.modules.chat.service import ChatService
from app.modules.analytics.service import AnalyticsService

def get_auth_service(
    db: AsyncDatabase = Depends(get_database),
) -> AuthService:
    return AuthService(db)

def get_document_service(
    db=Depends(get_database),
):
    return DocumentService(db)

def get_search_service(
    db=Depends(get_database),
):
    return SearchService(db)

def get_document_content_service(
    db=Depends(get_database),
):
    return DocumentContentService(db)

def get_chat_service(
    db=Depends(get_database),
):
    return ChatService(db)

def get_analytics_service(
    db = Depends(get_database),
):
    return AnalyticsService(db)