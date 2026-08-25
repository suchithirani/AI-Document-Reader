from app.services.image_query.service import ImageQueryService
from app.services.page_query.service import PageQueryService


def test_page_query_service_multilingual():
    service = PageQueryService()

    # 1. English
    assert service.extract_page_numbers("What is written on page 3?") == [3]
    assert service.extract_page_numbers("Check pages 2, 4, 5") == [2, 4, 5]
    assert service.extract_page_numbers("from page #7") == [7]

    # 2. Hindi / Hinglish
    assert service.extract_page_numbers("पेज नंबर 2 पर क्या है?") == [2]

    # 3. Gujarati
    assert service.extract_page_numbers("પેજ નંબર 4 જુઓ") == [4]

    # 4. No pages
    assert service.extract_page_numbers("Summarize this document") == []


def test_image_query_service():
    service = ImageQueryService()

    # Requires images (visual query)
    assert service.requires_images("Show me the chart on page 2") is True
    assert service.requires_images("Is there a diagram or figure?") is True
    assert service.requires_images("tasveer dikhao") is True
    assert service.requires_images("chitra check karo") is True

    # Does not require images (text query)
    assert service.requires_images("What is the invoice number?") is False
