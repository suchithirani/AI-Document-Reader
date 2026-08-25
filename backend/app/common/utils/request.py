from fastapi import Request


def get_request_info(
    request: Request,
) -> tuple[str | None, str | None]:
        ip_address = (
            request.client.host
            if request.client
            else None
        )

        user_agent = request.headers.get(
            "user-agent"
        )

        return ip_address, user_agent
