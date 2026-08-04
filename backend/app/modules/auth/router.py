from fastapi import APIRouter, Depends, Request, status

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


@auth_router.post("/register")
async def register(
    request: Request,
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.register(
        request,
        body,
    )

    return success_response(
        data=result,
        message="User registered successfully.",
        status_code=201,
    )


@auth_router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.login(request, body)

    return success_response(
        message="Login successful.",
        data=result,
    )


@auth_router.post("/refresh")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.refresh_token(request, body)

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
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.change_password(
        request,
        current_user,
        body
    )

    return success_response(
        message=result["message"],
    )


@auth_router.post("/logout")
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.logout(
        request,
        current_user,
        body,
    )

    return success_response(
        message=result["message"],
    )