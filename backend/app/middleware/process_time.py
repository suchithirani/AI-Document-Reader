import time

from fastapi import Request


async def process_time_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    response.headers["X-Process-Time"] = f"{process_time} ms"

    return response