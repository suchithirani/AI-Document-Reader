from datetime import UTC, datetime, timedelta
import hashlib
from typing import Any

import jwt
from passlib.context import CryptContext

from app.common.constants import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from app.core.config import settings
from app.common.exceptions.auth import UnauthorizedException

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    print(password)
    print(len(password))
    print(type(password))
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create an access JWT.
    """
    expire = (
        datetime.now(UTC)
        + (
            expires_delta
            or timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    payload = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a refresh JWT.
    """
    expire = (
        datetime.now(UTC)
        + (
            expires_delta
            or timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        )
    )

    payload = {
        "sub": subject,
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired.")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid token.")


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_token_expiry(token: str) -> datetime:
    payload = decode_token(token)
    return datetime.fromtimestamp(payload["exp"], tz=UTC)