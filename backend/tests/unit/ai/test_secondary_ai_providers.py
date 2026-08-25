from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.providers.groq import GroqAIService
from app.services.ai.providers.ollama import OllamaAIService
from app.services.ai.vision.groq import GroqVision
from app.services.ai.vision.ollama import OllamaVision
from app.services.embedding.ollama import OllamaEmbedding


@pytest.mark.asyncio
async def test_groq_ai_service_complete():
    service = GroqAIService()

    # 1. Answer question
    mock_choice = MagicMock()
    mock_choice.message.content = "Groq answered question."
    mock_usage = MagicMock(prompt_tokens=50, completion_tokens=20)
    service.client.chat.completions.create = MagicMock(
        return_value=MagicMock(choices=[mock_choice], usage=mock_usage)
    )

    res = await service.answer_question(prompt="Hello Groq")
    assert res["answer"] == "Groq answered question."


@pytest.mark.asyncio
async def test_ollama_ai_service_complete():
    service = OllamaAIService()

    mock_resp = MagicMock(
        status_code=200,
        json=lambda: {
            "message": {"content": "Ollama response"},
            "prompt_eval_count": 30,
            "eval_count": 15,
        }
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await service.answer_question(prompt="Hello Ollama")
        assert res["answer"] == "Ollama response"


@pytest.mark.asyncio
async def test_groq_vision_and_ollama_vision():
    groq_vision = GroqVision()
    ollama_vision = OllamaVision()
    images = [{"bytes": b"\x89PNG\r\n\x1a\nfakebytes", "format": "png", "page_number": 1}]

    # Groq Vision
    mock_choice = MagicMock()
    mock_choice.message.content = "Visual bar chart description."
    groq_vision.client.chat.completions.create = MagicMock(
        return_value=MagicMock(choices=[mock_choice])
    )
    res_g = await groq_vision.analyze_images(prompt="Describe chart", images=images)
    assert "bar chart" in res_g

    # Ollama Vision
    mock_resp = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": "Ollama saw chart."}}
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res_o = await ollama_vision.analyze_images(prompt="What is this?", images=images)
        assert "chart" in res_o


@pytest.mark.asyncio
async def test_ollama_embedding_complete():
    embedding = OllamaEmbedding()
    mock_resp = MagicMock(
        status_code=200,
        json=lambda: {"embeddings": [[0.05] * 768]}
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        vec = await embedding.create_embedding("Sample text")
        assert len(vec) == 768
