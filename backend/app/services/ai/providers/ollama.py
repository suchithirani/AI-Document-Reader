import time
import httpx

from app.common.exceptions.ai import (
    AIAuthenticationException,
    AIResponseException,
)
from app.core.config import settings


class OllamaAIService:
    """Ollama provider for local text generation."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_GENERATION_MODEL
        self.timeout = httpx.Timeout(300.0)

    async def answer_question(
        self,
        prompt: str,
    ) -> dict:
        """
        Generate a text response using local Ollama.

        Args:
            prompt: Prompt sent to the model.

        Returns:
            Generated answer and usage information.
        """
        try:
            start = time.perf_counter()

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if response.status_code != 200:
                    raise AIResponseException(
                        f"Ollama returned status code {response.status_code}: {response.text}"
                    )

                data = response.json()

            latency = (
                time.perf_counter() - start
            ) * 1000

            answer = data.get("message", {}).get("content", "")
            
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens

            if not answer:
                raise AIResponseException(
                    "Empty response received from Ollama."
                )

            return {
                "answer": answer.strip(),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "latency_ms": round(
                    latency,
                    2,
                ),
            }

        except AIResponseException:
            raise

        except Exception as exception:
            message = str(exception)
            raise AIResponseException(
                f"Failed to communicate with Ollama: {message}"
            ) from exception

    async def answer_question_stream(
        self,
        prompt: str,
    ):
        import json
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": True,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    
                    if response.status_code != 200:
                        raise AIResponseException(
                            f"Ollama returned status code {response.status_code}"
                        )
                    
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content")
                            if content:
                                yield content

        except Exception as exception:
            message = str(exception)
            raise AIResponseException(
                f"Failed to stream from Ollama: {message}"
            ) from exception
