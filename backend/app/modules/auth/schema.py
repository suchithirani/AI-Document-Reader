from pydantic import ConfigDict, EmailStr, Field

from app.common.base_schema import BaseSchema
from app.common.constants import UserRole


# =====================================================================
# Request Schemas
# =====================================================================


class RegisterRequest(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(...,
    min_length=8,
    max_length=64,
)


class LoginRequest(BaseSchema):
    email: EmailStr

    password: str = Field(
    min_length=8,
    max_length=64,
)


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    current_password: str

    new_password: str = Field(..., min_length=8,max_length=64)

class AddPhoneRequest(BaseSchema):
    phone_number: str


class VerifyPhoneOtpRequest(BaseSchema):
    phone_number: str

    otp: str


class GoogleLoginRequest(BaseSchema):
    id_token: str


# =====================================================================
# Response Schemas
# =====================================================================


class UserResponse(BaseSchema):
    model_config = ConfigDict(
        populate_by_name=True,
    )

    id: str = Field(alias="_id")

    name: str

    email: EmailStr

    phone_number: str | None = None

    role: UserRole

    profile_picture: str | None = None

    is_active: bool

    is_verified: bool

    phone_verified: bool


class AuthResponse(BaseSchema):
    access_token: str

    refresh_token: str

    token_type: str = Field(default="Bearer")

    expires_in: int

    user: UserResponse