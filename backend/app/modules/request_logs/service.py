from app.common.utils.datetime import utc_now
from app.modules.request_logs.repository import RequestLogRepository


class RequestLogService:

    def __init__(self, db):
        self.repository = RequestLogRepository(db)

    async def log_request(
    self,
    *,
    request_id: str,
    user_id: str | None,
    method: str,
    path: str,
    query_params: dict,
    status_code: int,
    success: bool,
    error_message: str | None,
    response_time_ms: float,
    ip_address: str | None,
    user_agent: str | None,
    request_size: int | None,
    response_size: int | None,
):
        return await self.repository.create_log(
            {
                "request_id": request_id,
                "user_id": user_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "status_code": status_code,
                "success": success,
                "error_message": error_message,
                "response_time_ms": response_time_ms,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_size": request_size,
                "response_size": response_size,
                "timestamp": utc_now(),
            }
        )

    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
    ):
        return await self.repository.get_logs(
            skip,
            limit,
        )

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ):
        return await self.repository.get_user_logs(
            user_id,
            skip,
            limit,
        )

    async def count_logs(self):
        return await self.repository.count_logs()
