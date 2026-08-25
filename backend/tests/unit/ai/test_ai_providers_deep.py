from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.providers.gemini import GeminiAIService
from app.services.ai.providers.groq import GroqAIService
from app.services.ai.providers.ollama import OllamaAIService
from app.services.ai.summary_service import SummaryGenerationService
from app.services.ai.title_service import TitleGenerationService


@pytest.mark.asyncio
async def test_gemini_ai_service_provider():
    with patch("app.services.ai.providers.gemini.genai.Client") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        mock_resp = MagicMock()
        mock_resp.text = "Gemini answer text"
        mock_resp.usage_metadata.prompt_token_count = 10
        mock_resp.usage_metadata.candidates_token_count = 20
        mock_instance.models.generate_content.return_value = mock_resp

        service = GeminiAIService()
        res = await service.answer_question("Test prompt")
        assert res["answer"] == "Gemini answer text"
        assert res["prompt_tokens"] == 10
        assert res["completion_tokens"] == 20


@pytest.mark.asyncio
async def test_groq_ai_service_provider():
    with patch("app.services.ai.providers.groq.Groq") as MockGroq:
        mock_instance = MagicMock()
        MockGroq.return_value = mock_instance

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Groq answer text"))]
        mock_completion.usage.prompt_tokens = 15
        mock_completion.usage.completion_tokens = 25
        mock_instance.chat.completions.create.return_value = mock_completion

        service = GroqAIService()
        res = await service.answer_question("Test prompt")
        assert res["answer"] == "Groq answer text"
        assert res["prompt_tokens"] == 15


@pytest.mark.asyncio
async def test_ollama_ai_service_provider():
    service = OllamaAIService()
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": "Ollama answer text"},
            "prompt_eval_count": 8,
            "eval_count": 12,
        }
        mock_post.return_value = mock_resp

        res = await service.answer_question("Test prompt")
        assert res["answer"] == "Ollama answer text"


@pytest.mark.asyncio
async def test_summary_and_title_services(mock_db):
    mock_ai = MagicMock()
    mock_ai.answer_question = AsyncMock(
        return_value={
            "answer": "Summary text here",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms": 50.0,
        }
    )

    with patch("app.services.ai.summary_service.AIService", return_value=mock_ai):
        summary_svc = SummaryGenerationService(mock_db)
        summary = await summary_svc.generate_summary(conversation="User: Hi", session_id="s1")
        assert summary == "Summary text here"

    mock_ai.answer_question = AsyncMock(
        return_value={
            "answer": "Generated Title",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms": 50.0,
        }
    )
    with patch("app.services.ai.title_service.AIService", return_value=mock_ai):
        title_svc = TitleGenerationService(mock_db)
        title = await title_svc.generate_title(session_id="s1", question="What is this?", answer="This is a test.")
        assert title == "Generated Title"
