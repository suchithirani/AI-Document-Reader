from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions.document import OCRException
from app.services.document_images.pdf_image_extractor import PDFImageExtractor


def test_pdf_image_extractor_flow():
    extractor = PDFImageExtractor()

    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_images.return_value = [[123, 0, 100, 100, 8, "DeviceRGB", "", "img0", "DCTDecode"]]
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.extract_image.return_value = {
            "ext": "jpeg",
            "image": b"jpeg_bytes_here",
            "width": 200,
            "height": 200,
        }
        mock_fitz_open.return_value = mock_doc

        images = extractor.extract_images("dummy_test.pdf")
        assert len(images) == 1
        assert images[0]["page_number"] == 1
        assert images[0]["extension"] == "jpeg"
        assert images[0]["image_bytes"] == b"jpeg_bytes_here"


def test_pdf_image_extractor_error():
    extractor = PDFImageExtractor()
    with patch("fitz.open", side_effect=Exception("Corrupt PDF")):
        with pytest.raises(OCRException):
            extractor.extract_images("corrupt.pdf")
