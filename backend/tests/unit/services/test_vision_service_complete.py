from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.vision.service import VisionService


@pytest.mark.asyncio
async def test_vision_service_prompt_and_prepare():
    mock_image_service = MagicMock()
    mock_image_service.load_image_bytes = AsyncMock(return_value=b"fake_image_bytes")

    vision_service = VisionService(document_image_service=mock_image_service)

    # 1. Test build page prompt
    prompt = vision_service._build_page_prompt(prompt="Describe the logo", page_number=2)
    assert "Page number: 2" in prompt
    assert "Describe the logo" in prompt

    # 2. Test prepare images
    raw_images = [
        {
            "document_id": "doc1",
            "page_number": 2,
            "image_index": 0,
            "extension": "png",
        }
    ]
    prepared = await vision_service._prepare_images(raw_images)
    assert len(prepared) == 1
    assert prepared[0]["bytes"] == b"fake_image_bytes"
    assert prepared[0]["extension"] == "png"


@pytest.mark.asyncio
async def test_vision_service_analyze_page_batch_success_and_timeout():
    mock_image_service = MagicMock()
    vision_service = VisionService(document_image_service=mock_image_service)

    # Success
    vision_service.vision_router.analyze_images = AsyncMock(return_value="Chart shows 40% growth.")
    result = await vision_service._analyze_page_batch(
        page_prompt="Analyze chart",
        batch=[{"bytes": b"...", "extension": "png"}],
        page_number=1,
    )
    assert result == "Chart shows 40% growth."

    # Timeout
    async def mock_timeout(*args, **kwargs):
        raise TimeoutError()
    vision_service.vision_router.analyze_images = AsyncMock(side_effect=mock_timeout)
    timed_out_res = await vision_service._analyze_page_batch(
        page_prompt="Analyze chart",
        batch=[{"bytes": b"...", "extension": "png"}],
        page_number=1,
    )
    assert timed_out_res == ""
