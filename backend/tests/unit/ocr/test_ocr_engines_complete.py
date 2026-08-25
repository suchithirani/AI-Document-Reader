from unittest.mock import patch

import pytest

from app.ocr.factory import OCRFactory
from app.ocr.service import OCRService


def test_ocr_factory_and_service():
    pdf_engine = OCRFactory.get_engine(".pdf")
    assert pdf_engine is not None

    png_engine = OCRFactory.get_engine(".png")
    assert png_engine is not None

    jpg_engine = OCRFactory.get_engine(".jpg")
    assert jpg_engine is not None

    with pytest.raises(ValueError, match="Unsupported file type"):
        OCRFactory.get_engine(".xyz")

    # Test OCRService
    service = OCRService()
    with patch.object(pdf_engine, "extract_text", return_value=["Page 1 extracted text."]):
        with patch.object(OCRFactory, "get_engine", return_value=pdf_engine):
            text = service.extract_text("dummy.pdf", ".pdf")
            assert len(text) == 1
            assert text[0] == "Page 1 extracted text."
