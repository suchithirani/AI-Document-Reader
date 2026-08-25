import logging
import time

from fastapi import Request

logger = logging.getLogger(__name__)


async def logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    status_code = 500
    response = None


    try:
        response = await call_next(request)
        status_code = response.status_code
        return response


    finally:
        error_message = getattr(
        request.state,
        "error_message",
        None,
        )
        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

        user = getattr(request.state, "user", None)

        user_id = (
            str(user.id)
            if user is not None
            else None
        )

        request_size = request.headers.get(
            "content-length"
        )

        response_size = (
            response.headers.get("content-length")
            if response
            else None
        )

        try:
            service = request.app.state.request_log_service

            await service.log_request(
                request_id=request.state.request_id,
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                status_code=status_code,
                success=status_code < 400,
                error_message=error_message,
                response_time_ms=round(response_time_ms, 2),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_size=int(request_size) if request_size else None,
                response_size=int(response_size) if response_size else None,
            )

        except Exception:
            logger.exception(
                "Failed to save request log."
            )

        logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            status_code,
            response_time_ms,
        )

        if error_message:
            logger.error(
                "Request failed: %s",
                error_message,
            )
