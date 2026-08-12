import logging
from fastapi import Request

from app.common.exceptions.auth import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    AccountLockedException,
)
from app.common.utils.datetime import utc_now
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.modules.auth.model import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schema import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendOtpRequest,
    UserResponse,
    VerifyOtpRequest,
)
from app.common.utils.request import get_request_info
from app.modules.auth.refresh_repository import RefreshTokenRepository
from app.common.constants import AuditAction, AuditResource
from app.modules.audit_logs.service import AuditLogService
from app.services.rate_limit.auth_lockout import (
    AuthLockoutService,
)

from app.services.email.queue_service import (
    EmailQueueService,
)

from app.services.otp.service import OtpService

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, db):
        self.user_repository = UserRepository(db)
        self.refresh_repository = RefreshTokenRepository(db)
        self.audit_log_service = AuditLogService(db)
        self.lockout = AuthLockoutService()
        self.email_queue = EmailQueueService()
        self.otp_service = OtpService()

    def _generate_auth_response(self, user: User, access_token: str, refresh_token: str) -> AuthResponse:

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                _id=user.id,
                name=user.name,
                email=user.email,
                phone_number=user.phone_number,
                role=user.role,
                profile_picture=user.profile_picture,
                is_active=user.is_active,
                is_verified=user.is_verified,
                phone_verified=user.phone_verified,
            ),
        )

    async def register(
        self,
        http_request: Request,
        request: RegisterRequest,
    ) -> AuthResponse:
        
        existing_user = await self.user_repository.get_by_email(
            request.email
        )

        if existing_user:
            raise BadRequestException(
                "Email already registered."
            )

        now = utc_now()

        user = User(
            name=request.name,
            email=request.email,
            password_hash=hash_password(request.password),
            created_at=now,
            updated_at=now,
        )

        created_user = await self.user_repository.create_user(
            user.model_dump(
                by_alias=True,
                exclude_none=True,
            )
        )

        otp = await self.otp_service.generate(
            created_user.email,
        )

        await self.email_queue.send_verification_email(
            email=created_user.email,
            otp=otp,
        )
        
        return {
            "message": (
                "Registration successful. "
                "Please verify your email using the OTP sent to your email."
            ),
        }

    async def login(
        self,
        http_request: Request,
        request: LoginRequest,
    ) -> AuthResponse:

        identifier = request.email.strip().lower()
        user = await self.user_repository.get_by_email(
            identifier
        )
        if not user:
            raise UnauthorizedException(
                "Invalid email or password."
            )
        if not user.is_verified:
            raise ForbiddenException(
                "Please verify your email before logging in.",
            )


        if not user.is_active:
            raise UnauthorizedException(
                "Account is inactive."
            )
        if await self.lockout.is_locked(
            identifier,
        ):
            raise AccountLockedException()
        if not verify_password(
            request.password,
            user.password_hash,
        ):

            await self.lockout.record_failure(
                identifier,
            )

            raise UnauthorizedException(
                "Invalid email or password."
            )
        await self.lockout.reset_failures(
            identifier,
        )
        await self.user_repository.update_last_login(
            str(user.id)
        )

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        ip_address, user_agent = get_request_info(
        http_request
)
        await self.refresh_repository.create_refresh_token(
        {
            "user_id": str(user.id),
            "token_hash": hash_refresh_token(refresh_token),
            "revoked": False,
            "expires_at": get_token_expiry(refresh_token),
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    )
        await self.audit_log_service.create_log(
        user_id=str(user.id),
        action=AuditAction.LOGIN,
        resource=AuditResource.AUTH,
        description="User logged in successfully.",
        metadata={
            "email": user.email,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

        return self._generate_auth_response(
            user,
            access_token,
            refresh_token,
        )

    async def refresh_token(
    self,
    http_request: Request,
    request: RefreshTokenRequest,
) -> AuthResponse:
        ip_address, user_agent = get_request_info(
            http_request
        )
        token_hash = hash_refresh_token(request.refresh_token)
        token = await self.refresh_repository.get_by_token_hash(
            token_hash
        )

        if token is None:
            raise UnauthorizedException(
                "Invalid refresh token."
            )

        if token.revoked:

            await self.refresh_repository.revoke_all_user_tokens(
                token.user_id,
            )

            await self.audit_log_service.create_log(
                user_id=token.user_id,
                action=AuditAction.REFRESH_TOKEN,
                resource=AuditResource.AUTH,
                description="Refresh token reuse detected.",
                metadata={
                    "reason": "Refresh token reuse detected. All tokens revoked.",
                    "token_reuse": True,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            raise UnauthorizedException(
                "Refresh token reuse detected. Please login again."
            )

        payload = decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedException(
                "Refresh token required."
            )
        

        user = await self.user_repository.get_by_id(
            payload["sub"]
        )

        if user is None:
            raise NotFoundException(
                "If an account exists, a password reset OTP has been sent."
            )

        if not user.is_active:
            raise UnauthorizedException(
                "Account is inactive."
            )

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        await self.refresh_repository.revoke_refresh_token(
            token_hash
        )

        await self.refresh_repository.create_refresh_token(
            {
                "user_id": str(user.id),
                "token_hash": hash_refresh_token(refresh_token),
                "revoked": False,
                "expires_at": get_token_expiry(refresh_token),
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        await self.audit_log_service.create_log(
        user_id=str(user.id),
        action=AuditAction.REFRESH_TOKEN,
        resource=AuditResource.AUTH,
        description="Access token refreshed.",
        metadata={
            "email": user.email,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

        return self._generate_auth_response(
            user,
            access_token,
            refresh_token,
        )

    async def verify_email(
        self,
        http_request: Request,
        request: VerifyOtpRequest,
    ) -> AuthResponse:

        user = await self.user_repository.get_by_email(
            request.identifier,
        )

        if user is None:
            raise NotFoundException(
                "If an account exists, a password reset OTP has been sent.",
            )

        if user.is_verified:
            raise BadRequestException(
                "Email already verified.",
            )

        verified = await self.otp_service.verify_and_delete(
            identifier=request.identifier,
            otp=request.otp,
        )

        if not verified:
            raise BadRequestException(
                "Invalid or expired OTP.",
            )

        await self.user_repository.verify_email(
            str(user.id),
        )
        access_token = create_access_token(
            str(user.id),
        )
        refresh_token = create_refresh_token(
            str(user.id),
        )
        await self.user_repository.update_last_login(
            str(user.id),
        )

        await self.refresh_repository.create_refresh_token(
            {
                "user_id": str(user.id),
                "token_hash": hash_refresh_token(
                    refresh_token,
                ),
                "revoked": False,
                "expires_at": get_token_expiry(
                    refresh_token,
                ),
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        ip_address, user_agent = get_request_info(
            http_request,
        )

        await self.audit_log_service.create_log(
            user_id=str(user.id),
            action=AuditAction.EMAIL_VERIFY,
            resource=AuditResource.AUTH,
            description="Email verified successfully.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.email_queue.send_welcome_email(
            username=user.name,
            email=user.email,
        )
        verified_user = await self.user_repository.get_by_id(
            str(user.id),
        )

        return self._generate_auth_response(
            verified_user,
            access_token,
            refresh_token,
        )

    async def resend_verification_otp(
        self,
        request: SendOtpRequest,
    ) -> dict:
        user = await self.user_repository.get_by_email(
            request.identifier,
        )

        if user is None:
            raise NotFoundException(
                "If an account exists, a password reset OTP has been sent.",
            )

        if user.is_verified:
            raise BadRequestException(
                "Email already verified.",
            )
        allowed = await self.otp_service.can_resend(
            request.identifier,
        )

        if not allowed:

            retry_after = (
                await self.otp_service.resend_after(
                    request.identifier,
                )
            )

            raise BadRequestException(
                (
                    "OTP already sent. "
                    f"Try again in {retry_after} seconds."
                )
            )
        otp = await self.otp_service.generate(
            request.identifier,
        )

        await self.email_queue.send_verification_email(
            email=user.email,
            otp=otp,
        )

        return {
            "message": "Verification OTP sent successfully.",
        }

    async def forgot_password(
        self,
        request: ForgotPasswordRequest,
    ):
        user = await self.user_repository.get_by_email(
            request.identifier,
        )

        if user is None:
            raise NotFoundException(
                "If an account exists, a password reset OTP has been sent.",
            )

        otp = await self.otp_service.generate(
            request.identifier,
        )

        await self.email_queue.send_forgot_password_email(
            email=user.email,
            otp=otp,
        )

        return {
            "message": "Password reset OTP sent successfully.",
        }

    async def get_current_user(self, current_user: User) -> UserResponse:
        return UserResponse(
            _id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            phone_number=current_user.phone_number,
            role=current_user.role,
            profile_picture=current_user.profile_picture,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            phone_verified=current_user.phone_verified,
        )

    async def reset_password(
        self,
        http_request: Request,
        request: ResetPasswordRequest,
    ):
        user = await self.user_repository.get_by_email(
            request.identifier,
        )

        if user is None:
            raise NotFoundException(
                "User not found.",
            )
        verified = await self.otp_service.verify(
            identifier=request.identifier,
            otp=request.otp,
        )

        if not verified:
            raise BadRequestException(
                "Invalid or expired OTP.",
            )


        if verify_password(
            request.new_password,
            user.password_hash,
        ):
            raise BadRequestException(
                "New password must be different from the current password.",
            )

        await self.user_repository.update_password(
            str(user.id),
            hash_password(
                request.new_password,
            ),
        )
        

        await self.refresh_repository.revoke_all_user_tokens(
            str(user.id),
        )
        

        ip_address, user_agent = get_request_info(
            http_request,
        )

        await self.audit_log_service.create_log(
            user_id=str(user.id),
            action=AuditAction.CHANGE_PASSWORD,
            resource=AuditResource.AUTH,
            description="Password changed successfully.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        

        await self.email_queue.send_password_changed_email(
            user.email,
        )
        verified = await self.otp_service.verify_and_delete(
                    identifier=request.identifier,
                    otp=request.otp,
                )

        return {
            "message": "Password changed successfully.",
        }

    async def logout(
        self,
        http_request: Request,
        current_user: User,
        request: RefreshTokenRequest,
    ) -> dict:

        token_hash = hash_refresh_token(request.refresh_token)
        token = await self.refresh_repository.get_by_token_hash(
            token_hash
        )

        if token is None:
            raise UnauthorizedException(
                "Invalid refresh token."
            )

        if token.user_id != str(current_user.id):
            raise UnauthorizedException(
                "Refresh token does not belong to the current user."
            )

        if token.revoked:
            raise UnauthorizedException(
                "Refresh token has already been revoked."
            )

        await self.refresh_repository.revoke_refresh_token(
            token_hash
        )

        ip_address, user_agent = get_request_info(
            http_request
        )
        await self.audit_log_service.create_log(
            user_id=str(current_user.id),
            action=AuditAction.LOGOUT,
            resource=AuditResource.AUTH,
            description="User logged out successfully.",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "message": "Logged out successfully."
        }