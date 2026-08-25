from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.vision.gemini import GeminiVision
from app.services.ai.vision.groq import GroqVision
from app.services.ai.vision.ollama import OllamaVision
from app.services.ai.vision.router import VisionRouter


@pytest.mark.asyncio
async def test_gemini_vision_provider():
    with patch("app.services.ai.vision.gemini.genai.Client") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        mock_resp = MagicMock()
        mock_resp.text = "Bar chart with revenue"
        mock_instance.aio.models.generate_content = AsyncMock(return_value=mock_resp)

        provider = GeminiVision()
        images = [{"bytes": b"img_bytes", "extension": "png"}]
        result = await provider.analyze_images("Describe image", images)
        assert result == "Bar chart with revenue"


@pytest.mark.asyncio
async def test_groq_vision_provider():
    with patch("app.services.ai.vision.groq.Groq") as MockGroq:
        mock_instance = MagicMock()
        MockGroq.return_value = mock_instance

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Pie chart analysis"))]
        mock_instance.chat.completions.create.return_value = mock_completion

        provider = GroqVision()
        images = [{"bytes": b"img_bytes", "extension": "jpeg"}]
        result = await provider.analyze_images("Describe chart", images)
        assert result == "Pie chart analysis"


@pytest.mark.asyncio
async def test_ollama_vision_provider():
    provider = OllamaVision()
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": "Ollama vision chart output"}}
        mock_post.return_value = mock_resp

        images = [{"bytes": b"img_bytes", "extension": "png"}]
        result = await provider.analyze_images("Describe chart", images)
        assert result == "Ollama vision chart output"


@pytest.mark.asyncio
async def test_vision_router_failover():
    mock_prov1 = MagicMock()
    mock_prov1.analyze_images = AsyncMock(side_effect=Exception("Rate limit"))

    mock_prov2 = MagicMock()
    mock_prov2.analyze_images = AsyncMock(return_value="Provider 2 result")

    router = VisionRouter(providers=[mock_prov1, mock_prov2])
    images = [{"bytes": b"...", "extension": "png"}]

    res = await router.analyze_images("prompt", images)
    assert res == "Provider 2 result"
