from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.exceptions.auth import (
    NotFoundException,
    UnauthorizedException,
)
from app.core.database import get_database
from app.core.security import decode_token
from app.modules.auth.repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_database),
):
    token = credentials.credentials  # <-- Extract the JWT string

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid access token.")

    user_id = payload.get("sub")

    if not user_id:
        raise UnauthorizedException("Invalid token payload.")

    repository = UserRepository(db)

    user = await repository.get_by_id(user_id)

    if not user:
        raise NotFoundException("User not found.")

    if not user.is_active:
        raise UnauthorizedException("User is inactive")

    request.state.user = user
    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    return current_user
