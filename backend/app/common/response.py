from typing import Any


def success_response(
    message: str,
    data: Any = None,
):
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def created_response(
    message: str,
    data: Any = None,
):
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
):
    return {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        },
    }