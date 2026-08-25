from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.vision.router import VisionRouter
from app.services.vision.service import VisionService


@pytest.mark.asyncio
async def test_vision_service_complete_lifecycle():
    mock_doc_img_service = MagicMock()
    mock_doc_img_service.load_image_bytes = AsyncMock(return_value=b"fake_image_bytes")

    service = VisionService(mock_doc_img_service)

    # 1. Test _build_page_prompt variations
    p1 = service._build_page_prompt("custom query", 1)
    assert "custom query" in p1
    assert "Page number: 1" in p1

    from app.services.ai.prompts.vision_prompt import VISION_ANALYSIS_PROMPT
    p2 = service._build_page_prompt(VISION_ANALYSIS_PROMPT, 2)
    assert "Describe and identify" in p2

    # 2. Test _prepare_images
    images = [
        {"document_id": "d1", "page_number": 1, "image_index": 0, "extension": "png"},
        {"document_id": "d1", "page_number": 1, "image_index": 1},
    ]
    prep = await service._prepare_images(images)
    assert len(prep) == 2

    # Empty bytes skip
    mock_doc_img_service.load_image_bytes = AsyncMock(return_value=None)
    prep_empty = await service._prepare_images(images)
    assert len(prep_empty) == 0

    # 3. Test _analyze_page_batch (Success, Timeout, Exception)
    service.vision_router.analyze_images = AsyncMock(return_value="Detected chart data")
    res_ok = await service._analyze_page_batch("prompt", prep, 1)
    assert res_ok == "Detected chart data"

    # Timeout simulation
    async def slow_analyze(*args, **kwargs):
        raise TimeoutError()
    service.vision_router.analyze_images = slow_analyze
    res_timeout = await service._analyze_page_batch("prompt", prep, 1)
    assert res_timeout == ""

    # Exception simulation
    service.vision_router.analyze_images = AsyncMock(side_effect=RuntimeError("Provider failed"))
    res_err = await service._analyze_page_batch("prompt", prep, 1)
    assert res_err == ""

    # 4. Test analyze_images_by_page and analyze_images
    mock_doc_img_service.load_image_bytes = AsyncMock(return_value=b"fake_image_bytes")
    service.vision_router.analyze_images = AsyncMock(return_value="Detected chart")

    out = await service.analyze_images(images)
    assert "Page 1:" in out
    assert "Detected chart" in out

    # Empty images check
    assert (await service.analyze_images([])) == ""
    assert (await service.analyze_images_by_page([], "prompt")) == []


@pytest.mark.asyncio
async def test_vision_router_providers():
    p1 = MagicMock()
    p1.is_available = MagicMock(return_value=True)
    p1.analyze_images = AsyncMock(return_value="Result from p1")

    p2 = MagicMock()
    p2.is_available = MagicMock(return_value=True)
    p2.analyze_images = AsyncMock(return_value="Result from p2")

    router = VisionRouter(providers=[p1, p2])

    # 1. Normal execution
    res = await router.analyze_images(prompt="test", images=[{"bytes": b"123", "extension": "png"}])
    assert res == "Result from p1"

    # 2. Fallback to p2 on p1 failure
    p1.analyze_images = AsyncMock(side_effect=Exception("P1 Rate Limit 429"))
    res_fallback = await router.analyze_images(prompt="test", images=[{"bytes": b"123", "extension": "png"}])
    assert res_fallback == "Result from p2"
