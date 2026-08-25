from unittest.mock import MagicMock, patch

from app.ocr.pdf import PDFOCR


def test_pdf_ocr_clean_text():
    pdf_ocr = PDFOCR()
    res = pdf_ocr._clean_text("  Line 1   \n\n\n  Line 2  ")
    assert "Line 1" in res
    assert "Line 2" in res
    assert pdf_ocr._clean_text("") == ""


def test_pdf_ocr_scanned_fallback():
    pdf_ocr = PDFOCR()
    mock_page = MagicMock()
    mock_page.find_tables.return_value = []
    mock_page.get_text.return_value = []  # No digital text -> triggers OCR fallback

    # Mock pixmap
    mock_pix = MagicMock(width=100, height=100, samples=b"\xff" * 30000)
    mock_page.get_pixmap.return_value = mock_pix

    with patch("pytesseract.image_to_string", return_value="Scanned invoice text"):
        text = pdf_ocr._extract_with_ocr(mock_page)
        assert text == "Scanned invoice text"
