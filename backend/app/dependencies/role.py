from fastapi import Depends

from app.common.constants import UserRole
from app.common.exceptions.auth import ForbiddenException
from app.dependencies.auth import get_current_user


class RoleChecker:
    def __init__(
        self,
        *allowed_roles: UserRole,
    ):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user=Depends(get_current_user),
    ):
        user_role = current_user.role if hasattr(current_user, "role") else current_user.get("role")
        if user_role not in self.allowed_roles:
            raise ForbiddenException(
                "You don't have permission to access this resource."
            )

        return current_user


AdminOnly = RoleChecker(
    UserRole.ADMIN,
)

UserOnly = RoleChecker(
    UserRole.USER,
)

AdminOrUser = RoleChecker(
    UserRole.ADMIN,
    UserRole.USER,
)
