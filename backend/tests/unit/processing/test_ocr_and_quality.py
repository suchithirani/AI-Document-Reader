import numpy as np
import pytest

from app.ocr.factory import OCRFactory
from app.ocr.image import ImageOCR
from app.ocr.pdf import PDFOCR
from app.ocr.quality import compute_image_metrics


def test_compute_image_metrics_high_quality():
    # Synthetic checkerboard image with sharp edges (high Laplacian variance & contrast)
    img = np.zeros((100, 100), dtype=np.float64)
    img[::2, ::2] = 255.0
    img[1::2, 1::2] = 255.0

    score = compute_image_metrics(img)
    assert 50.0 <= score <= 100.0


def test_compute_image_metrics_flat_blurry():
    # Completely flat image (zero variance, zero contrast)
    img = np.ones((100, 100), dtype=np.float64) * 128.0
    score = compute_image_metrics(img)
    assert score < 20.0


def test_ocr_factory_engine_selection():
    assert isinstance(OCRFactory.get_engine(".pdf"), PDFOCR)
    assert isinstance(OCRFactory.get_engine(".PDF"), PDFOCR)
    assert isinstance(OCRFactory.get_engine(".png"), ImageOCR)
    assert isinstance(OCRFactory.get_engine(".jpg"), ImageOCR)
    assert isinstance(OCRFactory.get_engine(".jpeg"), ImageOCR)


def test_ocr_factory_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported file type"):
        OCRFactory.get_engine(".exe")
