from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request, Response

from app.middleware.logging import logging_middleware


@pytest.mark.asyncio
async def test_logging_middleware_success():
    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.request_id = "req-123"
    mock_request.state.user = None
    mock_request.state.error_message = None
    mock_request.headers = {"content-length": "100"}
    mock_request.method = "GET"
    mock_request.url = MagicMock(path="/api/v1/health")
    mock_request.client = MagicMock(host="127.0.0.1")

    mock_log_service = MagicMock()
    mock_log_service.log_request = AsyncMock()
    mock_request.app.state.request_log_service = mock_log_service

    mock_response = Response(content="OK", status_code=200, headers={"content-length": "2"})

    async def mock_call_next(req):
        return mock_response

    resp = await logging_middleware(mock_request, mock_call_next)
    assert resp.status_code == 200
    assert mock_log_service.log_request.called
