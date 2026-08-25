from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    *,
    message: str,
    data: Any = None,
    status_code: int = 200,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
        },
    )


def created_response(
    *,
    message: str,
    data: Any = None,
):
    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
        },
    )


def paginated_response(
    *,
    items: list,
    total: int,
    page: int,
    limit: int,
):
    return JSONResponse(
        content={
            "success": True,
            "data": jsonable_encoder(items),
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
            },
        },
    )
