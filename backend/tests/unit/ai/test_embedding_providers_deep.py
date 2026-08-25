from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.embedding.gemini import GeminiEmbedding
from app.services.embedding.local import LocalEmbedding
from app.services.embedding.ollama import OllamaEmbedding
from app.services.embedding.openai import OpenAIEmbedding
from app.services.embedding.service import EmbeddingService


@pytest.mark.asyncio
async def test_gemini_embedding_provider():
    with patch("app.services.embedding.gemini.genai.Client") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        mock_resp = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 768
        mock_resp.embeddings = [mock_embedding, mock_embedding]
        mock_instance.models.embed_content.return_value = mock_resp

        provider = GeminiEmbedding()
        vec = await provider.create_embedding("test text")
        assert len(vec) == 768

        vecs = await provider.create_embeddings(["text 1", "text 2"])
        assert len(vecs) == 2


@pytest.mark.asyncio
async def test_ollama_embedding_provider():
    provider = OllamaEmbedding()
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": [[0.05] * 768]}
        mock_post.return_value = mock_resp

        vec = await provider.create_embedding("test query")
        assert len(vec) == 768


@pytest.mark.asyncio
async def test_openai_and_local_embedding_stubs():
    openai_emb = OpenAIEmbedding()
    with pytest.raises(NotImplementedError):
        await openai_emb.create_embedding("query")

    local_emb = LocalEmbedding()
    with pytest.raises(NotImplementedError):
        await local_emb.create_embedding("query")


@pytest.mark.asyncio
async def test_embedding_service_facade():
    mock_engine = MagicMock()
    mock_engine.create_embedding = AsyncMock(return_value=[0.2] * 768)
    mock_engine.create_embeddings = AsyncMock(return_value=[[0.2] * 768])

    with patch("app.services.embedding.factory.EmbeddingFactory.get_engine", return_value=mock_engine):
        service = EmbeddingService(provider="gemini")
        vec = await service.create_embedding("test query")
        assert len(vec) == 768

        vecs = await service.create_embeddings(["test chunk"])
        assert len(vecs) == 1
