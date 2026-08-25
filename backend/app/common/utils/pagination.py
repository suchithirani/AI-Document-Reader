from app.common.constants import DEFAULT_LIMIT, DEFAULT_PAGE


def paginate(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_LIMIT,
) -> tuple[int, int]:
    """
    Calculate skip and limit values.
    """
    skip = (page - 1) * limit
    return skip, limit
