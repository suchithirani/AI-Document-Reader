from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.core.database import get_database

from app.modules.auth.service import AuthService


def get_auth_service(
    db: AsyncDatabase = Depends(get_database),
) -> AuthService:
    return AuthService(db)