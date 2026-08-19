from groq import Groq
import asyncio
import base64
import time

from app.core.config import settings
from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)


class GroqAIService:

    VISION_MAX_COMPLETION_TOKENS = 1200

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY,max_retries=0)

    async def answer_question(self, prompt: str):
        try:
            start = time.perf_counter()

            completion = self.client.chat.completions.create(
                model=settings.GENERATION_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )

            latency = (time.perf_counter() - start) * 1000
            answer = completion.choices[0].message.content
            usage = completion.usage

            if not answer:
                raise AIResponseException(
                    "Empty response received from Groq."
                )

            return {
                "answer": answer.strip(),
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "latency_ms": round(latency, 2),
            }

        except AIResponseException:
            raise
        except Exception as exception:
            message = str(exception)
            lower = message.lower()

            if (
                "invalid api key" in lower
                or "expired_api_key" in lower
                or "unauthorized" in lower
                or "authentication" in lower
            ):
                raise AIAuthenticationException(message) from exception

            raise AIResponseException(message) from exception

    async def analyze_images(self, prompt: str, images: list[dict]) -> str:
        print("🔥 NEW GROQ VISION SERVICE CODE IS RUNNING 🔥")

        if not images:
            return ""

        try:
            print("VISION PROMPT:", repr(prompt))

            content = await self._build_vision_content(
                prompt=prompt,
                images=images,
            )

            for attempt in range(self.MAX_VISION_RETRIES + 1):
                try:
                    print(
                        f"Calling Groq Vision "
                        f"(attempt {attempt + 1})"
                    )

                    completion = self.client.chat.completions.create(
                        model=settings.VISION_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": content,
                            }
                        ],
                        # Increased from 600 because Qwen was
                        # exhausting the budget inside <think>.
                        max_completion_tokens=(
                            self.VISION_MAX_COMPLETION_TOKENS
                        ),
                        reasoning_effort="none",
                        reasoning_format="hidden"
                    )

                    answer = (
                        completion.choices[0].message.content
                        or ""
                    )

                    print("===== RAW VISION ANSWER =====")
                    print(repr(answer))
                    print("VISION ANSWER LENGTH:", len(answer))
                    print("==============================")

                    if not answer.strip():
                        raise AIResponseException(
                            "Empty vision response received from Groq."
                        )

                    cleaned_answer = self._clean_response(answer)

                    print("===== CLEANED VISION ANSWER =====")
                    print(repr(cleaned_answer))
                    print("==================================")

                    if not cleaned_answer:
                        if "<think>" in answer.lower():
                            raise AIResponseException(
                                "Vision model exhausted its completion "
                                "budget inside a reasoning block."
                            )

                        raise AIResponseException(
                            "Vision model returned no visible answer."
                        )

                    print("===== GROQ VISION RETURN =====")
                    print(repr(cleaned_answer))
                    print("================================")

                    return cleaned_answer.strip()

                except Exception as exception:
                    message = str(exception)
                    lower = message.lower()

                    if (
                        "429" in lower
                        or "rate limit" in lower
                        or "too many requests" in lower
                    ):
                        if attempt >= self.MAX_VISION_RETRIES:
                            raise AIResponseException(
                                "Groq Vision rate limit exceeded after retries."
                            ) from exception

                        wait_seconds = 2 ** attempt

                        print("Groq Vision rate limited.")
                        print(
                            f"Retry {attempt + 1}/"
                            f"{self.MAX_VISION_RETRIES} "
                            f"in {wait_seconds}s"
                        )


                    if (
                        "invalid api key" in lower
                        or "expired_api_key" in lower
                        or "unauthorized" in lower
                        or "authentication" in lower
                    ):
                        raise AIAuthenticationException(message) from exception

                    raise AIResponseException(message) from exception

        except AIResponseException:
            raise
        except AIAuthenticationException:
            raise
        except Exception as exception:
            raise AIResponseException(str(exception)) from exception

    async def _build_vision_content(
        self,
        prompt: str,
        images: list[dict],
    ) -> list[dict]:

        content = [
            {
                "type": "text",
                "text": prompt,
            }
        ]

        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }

        for image in images:
            image_bytes = image.get("bytes")

            if not image_bytes:
                raise AIResponseException(
                    "Image bytes are empty."
                )

            encoded_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            extension = (
                image.get("extension", "jpeg")
                .lower()
                .lstrip(".")
            )

            mime_type = mime_types.get(extension)

            if mime_type is None:
                raise AIResponseException(
                    f"Unsupported image format: {extension}"
                )

            data_url = (
                f"data:{mime_type};base64,{encoded_image}"
            )

            print(
                "VISION IMAGE:",
                image.get("page_number"),
                "| index:",
                image.get("image_index"),
                "| bytes:",
                len(image_bytes),
            )

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                    },
                }
            )

        return content

    def _clean_response(self, response: str) -> str:
        if not response:
            return ""

        response = response.strip()

        while True:
            lower = response.lower()
            start = lower.find("<think>")

            if start == -1:
                break

            end = lower.find("</think>", start)

            if end == -1:
                # Incomplete reasoning block: discard it.
                response = response[:start]
                break

            end += len("</think>")
            response = response[:start] + response[end:]

        return response.replace("</think>", "").strip()