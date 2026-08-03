import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)


async def logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    response_time_ms = (
        time.perf_counter() - start_time
    ) * 1000

    user = getattr(request.state, "user", None)

    user_id = (
        str(user.id)
        if user is not None
        else None
    )

    request_size = request.headers.get("content-length")
    response_size = response.headers.get("content-length")

    service = request.app.state.request_log_service

    await service.log_request(
        request_id=request.state.request_id,
        user_id=user_id,
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        status_code=response.status_code,
        response_time_ms=round(response_time_ms, 2),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_size=int(request_size) if request_size else None,
        response_size=int(response_size) if response_size else None,
    )

    logger.info(
        "%s %s %s %.2f ms",
        request.method,
        request.url.path,
        response.status_code,
        response_time_ms,
    )

    return response