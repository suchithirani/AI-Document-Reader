from fastapi import APIRouter, Depends, Request

from app.common.response import success_response
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import rate_limit
from app.dependencies.service import get_auth_service
from app.modules.auth.model import User
from app.modules.auth.schema import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendOtpRequest,
    VerifyOtpRequest,
)
from app.modules.auth.service import AuthService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@auth_router.post("/register",dependencies=[rate_limit(limit=5, window=60)],)
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

@auth_router.post(
    "/verify-email",
    dependencies=[rate_limit(limit=10, window=60)],
)
async def verify_email(
    request: Request,
    body: VerifyOtpRequest,
    service: AuthService = Depends(
        get_auth_service,
    ),
):

    result = await service.verify_email(
        request,
        body,
    )

    return success_response(
        message="Email verified successfully.",
        data=result,
    )

@auth_router.post("/resend-verification-otp",dependencies=[rate_limit(limit=3,window=300,),],
)
async def resend_verification_otp(
    body: SendOtpRequest,
    service: AuthService = Depends(
        get_auth_service,
    ),
):

    result = await service.resend_verification_otp(
        body,
    )

    return success_response(
        message=result["message"],
    )

@auth_router.post("/login",dependencies=[rate_limit(limit=10, window=60)],)
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

@auth_router.post("/refresh",dependencies=[rate_limit(limit=10, window=60)],)
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


@auth_router.get("/me",dependencies=[rate_limit(limit=10, window=60)],)
async def me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    result = await service.get_current_user(current_user)

    return success_response(
        message="User fetched successfully.",
        data=result,
    )

@auth_router.post("/forgot-password",dependencies=[
        rate_limit(limit=5, window=300,),],
)
async def forgot_password(
    body: ForgotPasswordRequest,
    service: AuthService = Depends(
        get_auth_service,
    ),
):

    result = await service.forgot_password(
        body,
    )

    return success_response(
        message=result["message"],
    )

@auth_router.post(
    "/reset-password",
    dependencies=[
        rate_limit(
            limit=5,
            window=300,
        ),
    ],
)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    service: AuthService = Depends(
        get_auth_service,
    ),
):

    result = await service.reset_password(
        request,
        body,
    )

    return success_response(
        message=result["message"],
    )

@auth_router.post("/logout",dependencies=[rate_limit(limit=30, window=60)],)
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
