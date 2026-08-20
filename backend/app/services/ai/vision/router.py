import asyncio
import logging
import time

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.services.ai.vision.provider import VisionProvider


logger = logging.getLogger(__name__)


class VisionRouter:
    """
    Routes vision requests across multiple providers.

    Features:
    - Automatic provider fallback
    - Temporary provider cooldown
    - Quota-aware routing
    - Retry handling
    - Prevents repeatedly calling an exhausted provider
    """

    PROVIDER_COOLDOWN_SECONDS = 60

    MAX_PROVIDER_RETRIES = 2

    RETRY_BASE_DELAY_SECONDS = 1

    def __init__(
        self,
        providers: list[VisionProvider],
    ):
        if not providers:
            raise ValueError(
                "At least one vision provider is required."
            )

        self.providers = providers

        # provider object -> timestamp until which it
        # should not be used
        self._cooldowns: dict[object, float] = {}

    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:

        if not images:
            return ""

        available_providers = (
            self._get_available_providers()
        )

        if not available_providers:

            logger.warning(
                "All vision providers are currently "
                "in cooldown. Retrying with primary provider."
            )

            # Avoid permanent deadlock.
            available_providers = [
                self.providers[0]
            ]

        last_exception: Exception | None = None

        for provider in available_providers:

            provider_name = (
                provider.__class__.__name__
            )

            for attempt in range(
                self.MAX_PROVIDER_RETRIES + 1
            ):

                try:

                    logger.info(
                        "Vision provider request: "
                        "provider=%s attempt=%s/%s",
                        provider_name,
                        attempt + 1,
                        self.MAX_PROVIDER_RETRIES + 1,
                    )

                    result = await provider.analyze_images(
                        prompt=prompt,
                        images=images,
                    )

                    if result:
                        self._clear_cooldown(provider)

                        logger.info(
                            "Vision provider success: "
                            "provider=%s",
                            provider_name,
                        )

                        return result

                    logger.warning(
                        "Vision provider returned empty "
                        "response: provider=%s",
                        provider_name,
                    )

                    last_exception = AIResponseException(
                        f"{provider_name} returned an empty response."
                    )

                    break

                except AIAuthenticationException:
                    raise

                except Exception as exception:

                    last_exception = exception

                    error_type = (
                        self._classify_error(
                            exception
                        )
                    )

                    logger.warning(
                        "Vision provider failed: "
                        "provider=%s attempt=%s/%s "
                        "type=%s error=%s",
                        provider_name,
                        attempt + 1,
                        self.MAX_PROVIDER_RETRIES + 1,
                        error_type,
                        exception,
                    )

                    # Permanent errors should immediately
                    # move to the next provider.
                    if error_type == "permanent":

                        logger.error(
                            "Vision permanent failure: "
                            "provider=%s",
                            provider_name,
                        )

                        break

                    # Quota errors should NOT be retried.
                    # Put provider into cooldown and
                    # immediately fallback.
                    if error_type == "quota":

                        self._set_cooldown(
                            provider,
                            self.PROVIDER_COOLDOWN_SECONDS,
                        )

                        logger.warning(
                            "Vision quota cooldown: "
                            "provider=%s cooldown=%ss",
                            provider_name,
                            self.PROVIDER_COOLDOWN_SECONDS,
                        )

                        break

                    # Temporary errors can be retried.
                    if error_type == "temporary":

                        if (
                            attempt
                            >= self.MAX_PROVIDER_RETRIES
                        ):
                            self._set_cooldown(
                                provider,
                                self.PROVIDER_COOLDOWN_SECONDS,
                            )

                            logger.warning(
                                "Vision temporary failure "
                                "retries exhausted: "
                                "provider=%s",
                                provider_name,
                            )

                            break

                        wait_seconds = (
                            self.RETRY_BASE_DELAY_SECONDS
                            * (2 ** attempt)
                        )

                        logger.info(
                            "Vision retry: "
                            "provider=%s retry_in=%ss",
                            provider_name,
                            wait_seconds,
                        )

                        await asyncio.sleep(
                            wait_seconds
                        )

        if last_exception is not None:
            raise AIResponseException(
                "All configured vision providers failed."
            ) from last_exception

        raise AIResponseException(
            "Vision analysis failed."
        )

    def _get_available_providers(
        self,
    ) -> list[VisionProvider]:

        now = time.monotonic()

        available = []

        for provider in self.providers:

            cooldown_until = (
                self._cooldowns.get(provider)
            )

            if (
                cooldown_until is not None
                and cooldown_until > now
            ):

                remaining = int(
                    cooldown_until - now
                )

                logger.debug(
                    "Vision provider in cooldown: "
                    "provider=%s remaining=%ss",
                    provider.__class__.__name__,
                    remaining,
                )

                continue

            if cooldown_until is not None:
                self._cooldowns.pop(
                    provider,
                    None,
                )

            available.append(provider)

        return available

    def _set_cooldown(
        self,
        provider: VisionProvider,
        seconds: int,
    ) -> None:

        self._cooldowns[provider] = (
            time.monotonic() + seconds
        )

    def _clear_cooldown(
        self,
        provider: VisionProvider,
    ) -> None:

        self._cooldowns.pop(
            provider,
            None,
        )

    @staticmethod
    def _classify_error(
        exception: Exception,
    ) -> str:

        message = str(exception).lower()

        # Authentication should be handled separately.
        if any(
            value in message
            for value in (
                "401",
                "403",
                "authentication",
                "unauthorized",
                "invalid api key",
                "api key not valid",
            )
        ):
            return "permanent"

        # Quota/rate-limit errors.
        if any(
            value in message
            for value in (
                "429",
                "quota",
                "resource exhausted",
                "rate limit",
                "too many requests",
                "daily limit",
                "free_tier_requests",
            )
        ):
            return "quota"

        # Temporary infrastructure failures.
        if any(
            value in message
            for value in (
                "503",
                "502",
                "500",
                "service unavailable",
                "temporarily unavailable",
                "timeout",
                "timed out",
                "connection reset",
                "connection error",
            )
        ):
            return "temporary"

        return "permanent"