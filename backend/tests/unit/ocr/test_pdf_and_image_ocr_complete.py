from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

from app.ocr.image import ImageOCR
from app.ocr.pdf import PDFOCR
from app.ocr.quality import compute_image_metrics


def test_pdf_ocr_table_to_markdown():
    pdf_ocr = PDFOCR()
    table = [
        ["Item", "Price", "Qty"],
        ["Laptop", "1000", "1"],
        ["Mouse", "20", "2"],
    ]
    md = pdf_ocr._table_to_markdown(table)
    assert "| Item | Price | Qty |" in md
    assert "| Laptop | 1000 | 1 |" in md

    # Empty table
    assert pdf_ocr._table_to_markdown([]) == ""


def test_pdf_ocr_extract_text():
    pdf_ocr = PDFOCR()
    with patch("fitz.open") as mock_fitz_open:
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        with patch.object(pdf_ocr, "_process_page_parallel", return_value="Page 1 text content"):
            pages = pdf_ocr.extract_text("sample.pdf")
            assert len(pages) == 1
            assert pages[0] == "Page 1 text content"


def test_image_ocr_preprocessing_and_extract():
    image_ocr = ImageOCR()

    # Create simple 100x100 RGB image
    img = Image.new("RGB", (100, 100), color="white")

    with patch("pytesseract.image_to_string", return_value="Extracted text from image"):
        res = image_ocr.extract_text(img)
        assert len(res) == 1
        assert res[0] == "Extracted text from image"


def test_ocr_quality_assessor():
    arr = np.ones((100, 100), dtype=np.float64) * 128
    score = compute_image_metrics(arr)
    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0
