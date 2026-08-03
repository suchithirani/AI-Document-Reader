from fastapi import APIRouter, Depends, status

from app.common.base_schema import MessageResponse
from app.common.response import created_response, success_response
from app.dependencies.auth import get_current_user
from app.dependencies.service import get_auth_service
from app.modules.auth.model import User
from app.modules.auth.schema import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.register(request)

    return created_response(
        message="User registered successfully.",
        data=result,
    )


@auth_router.post("/login")
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.login(request)

    return success_response(
        message="Login successful.",
        data=result,
    )


@auth_router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.refresh_token(request)

    return success_response(
        message="Token refreshed successfully.",
        data=result,
    )


@auth_router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.get_current_user(current_user)

    return success_response(
        message="User fetched successfully.",
        data=result,
    )


@auth_router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.change_password(
        current_user,
        request,
    )

    return success_response(
        message=result["message"],
    )


@auth_router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.logout(
        current_user=current_user,
        request=request,
    )

    return success_response(
        message=result["message"],
    )