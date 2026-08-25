from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.service import AIService


@pytest.mark.asyncio
async def test_ai_service_primary_and_fallback():
    with patch("app.services.ai.service.GeminiAIService") as MockGemini, \
         patch("app.services.ai.service.GroqAIService") as MockGroq, \
         patch("app.services.ai.service.OllamaAIService") as MockOllama, \
         patch("app.services.ai.service.VisionRouter"):

        mock_gemini = MagicMock()
        mock_groq = MagicMock()
        mock_ollama = MagicMock()

        MockGemini.return_value = mock_gemini
        MockGroq.return_value = mock_groq
        MockOllama.return_value = mock_ollama

        # 1. Primary succeeds
        mock_gemini.answer_question = AsyncMock(return_value={"answer": "Gemini response", "prompt_tokens": 10, "completion_tokens": 5, "latency_ms": 100})
        ai_service = AIService()
        res = await ai_service.answer_question("test prompt")
        assert res["answer"] == "Gemini response"

        # 2. Primary fails, fallback succeeds
        mock_gemini.answer_question = AsyncMock(side_effect=Exception("Rate limit 429"))
        mock_groq.answer_question = AsyncMock(return_value={"answer": "Groq fallback response", "prompt_tokens": 10, "completion_tokens": 5, "latency_ms": 100})

        res_fallback = await ai_service.answer_question("test prompt")
        assert res_fallback["answer"] == "Groq fallback response"
