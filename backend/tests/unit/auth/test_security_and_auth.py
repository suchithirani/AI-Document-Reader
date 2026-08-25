from datetime import timedelta

import pytest

from app.common.exceptions.auth import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hashing_and_verification():
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_decoding():
    subject = "user_12345"
    token = create_access_token(subject=subject)

    payload = decode_token(token)
    assert payload["sub"] == subject
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_creation_and_hash():
    subject = "user_12345"
    token = create_refresh_token(subject=subject)

    payload = decode_token(token)
    assert payload["sub"] == subject
    assert payload["type"] == "refresh"

    hashed = hash_refresh_token(token)
    assert len(hashed) == 64  # SHA256 length


def test_expired_token_raises_unauthorized():
    token = create_access_token(subject="user_123", expires_delta=timedelta(seconds=-10))
    with pytest.raises(UnauthorizedException, match="Token has expired"):
        decode_token(token)


def test_invalid_token_raises_unauthorized():
    with pytest.raises(UnauthorizedException, match="Invalid token"):
        decode_token("invalid.token.string")
