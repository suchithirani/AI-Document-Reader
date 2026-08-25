import tempfile
from pathlib import Path

import fitz

from app.ocr.pdf import PDFOCR


def test_pdf_ocr_table_to_markdown():
    ocr = PDFOCR()

    # 1. Empty table
    assert ocr._table_to_markdown([]) == ""
    assert ocr._table_to_markdown([[]]) == ""

    # 2. Valid table with headers and data
    table = [
        ["Item", "Qty", "Price"],
        ["Widget A", "2", "$10"],
        ["Widget B", "5"], # Shorter row test
    ]
    md = ocr._table_to_markdown(table)
    assert "| Item | Qty | Price |" in md
    assert "| --- | --- | --- |" in md
    assert "| Widget A | 2 | $10 |" in md
    assert "| Widget B | 5 |  |" in md


def test_pdf_ocr_synthetic_pdf_extraction():
    ocr = PDFOCR()

    # Create a small multi-page digital PDF in tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = tf.name

    doc = fitz.open()
    # Page 1: Digital text
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Hello world from PyMuPDF test extraction suite page 1!")

    # Page 2: Digital text
    page2 = doc.new_page()
    page2.insert_text((50, 50), "This is page 2 with additional digital content for testing parallel executor.")

    doc.save(pdf_path)
    doc.close()

    try:
        pages = ocr.extract_text(pdf_path)
        assert len(pages) == 2
        assert "Hello world" in pages[0]
        assert "page 2" in pages[1]
    finally:
        Path(pdf_path).unlink(missing_ok=True)
