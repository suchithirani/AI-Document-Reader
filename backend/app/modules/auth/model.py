from datetime import datetime

from pydantic import EmailStr, Field

from app.common.base_schema import BaseSchema
from app.common.constants import AuthProvider, UserRole


class User(BaseSchema):
    """
    User document model.
    """

    id: str | None = Field(default=None, alias="_id")

    name: str

    email: EmailStr

    phone_number: str | None = None

    password_hash: str

    role: UserRole = UserRole.USER

    auth_provider: AuthProvider = AuthProvider.LOCAL

    google_id: str | None = None

    profile_picture: str | None = None

    is_active: bool = True

    is_verified: bool = False

    phone_verified: bool = False

    last_login: datetime | None = None

    created_at: datetime

    updated_at: datetime