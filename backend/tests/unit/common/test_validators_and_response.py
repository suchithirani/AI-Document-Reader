import io

from fastapi import UploadFile

from app.common.response import (
    created_response,
    paginated_response,
    success_response,
)
from app.common.validators import (
    validate_content_type,
    validate_email,
    validate_file_extension,
    validate_filename,
    validate_password,
    validate_uuid,
)


def test_validate_email():
    assert validate_email("user@example.com") is True
    assert validate_email("invalid-email") is False
    assert validate_email("@missinguser.com") is False
    assert validate_email("user@.com") is False


def test_validate_password():
    assert validate_password("Valid123!") is True
    assert validate_password("short1!") is False  # < 8 chars
    assert validate_password("NoSpecial123") is False
    assert validate_password("nouppercase123!") is False
    assert validate_password("NOLOWERCASE123!") is False


def test_validate_uuid():
    assert validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True
    assert validate_uuid("invalid-uuid-string") is False


def test_validate_file_extension_and_mime():
    pdf_file = UploadFile(
        filename="test.pdf",
        file=io.BytesIO(b"%PDF-1.4 test"),
        headers={"content-type": "application/pdf"}
    )
    assert validate_filename(pdf_file) is True
    assert validate_file_extension(pdf_file) is True
    assert validate_content_type(pdf_file) is True

    bad_file = UploadFile(
        filename="script.exe",
        file=io.BytesIO(b"binary"),
        headers={"content-type": "application/x-msdownload"}
    )
    assert validate_file_extension(bad_file) is False
    assert validate_content_type(bad_file) is False


def test_response_helpers():
    resp_200 = success_response(message="Operation successful", data={"key": "val"})
    assert resp_200.status_code == 200

    resp_201 = created_response(message="Created", data={"id": 1})
    assert resp_201.status_code == 201

    resp_paginated = paginated_response(items=[{"id": 1}], total=10, page=1, limit=5)
    assert resp_paginated.status_code == 200
