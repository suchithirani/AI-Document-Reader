from unittest.mock import MagicMock

import pytest
from fastapi import Request, Response

from app.middleware.process_time import process_time_middleware
from app.middleware.request_id import request_id_middleware


@pytest.mark.asyncio
async def test_process_time_middleware():
    mock_req = MagicMock(spec=Request)
    mock_resp = Response(content="OK", status_code=200)

    async def mock_call_next(req):
        return mock_resp

    resp = await process_time_middleware(mock_req, mock_call_next)
    assert "X-Process-Time" in resp.headers
    assert "ms" in resp.headers["X-Process-Time"]


@pytest.mark.asyncio
async def test_request_id_middleware():
    mock_req = MagicMock(spec=Request)
    mock_req.state = MagicMock()
    mock_resp = Response(content="OK", status_code=200)

    async def mock_call_next(req):
        return mock_resp

    resp = await request_id_middleware(mock_req, mock_call_next)
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 10
