from unittest.mock import AsyncMock

import pytest

from app.common.exceptions.ai import AIResponseException
from app.services.ai.service import AIService


@pytest.mark.asyncio
async def test_ai_service_streaming_and_fallbacks():
    service = AIService()

    # 1. Answer question stream
    async def fake_stream(*args, **kwargs):
        yield "token1 "
        yield "token2"

    service.provider.answer_question_stream = fake_stream
    tokens = []
    async for t in service.answer_question_stream("prompt"):
        tokens.append(t)
    assert len(tokens) == 2

    # 2. Answer question with fallback
    service.provider.answer_question = AsyncMock(side_effect=AIResponseException("Primary failed"))
    if service.fallback_providers:
        service.fallback_providers[0].answer_question = AsyncMock(return_value={"answer": "Fallback success"})
    res = await service.answer_question("What is AI?")
    assert res is not None
