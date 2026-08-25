import numpy as np

from app.ocr.quality import (
    compute_image_metrics,
)


def test_quality_metrics_variations():
    # 1. Dark array
    dark_arr = np.zeros((50, 50), dtype=np.float64)
    score1 = compute_image_metrics(dark_arr)
    assert score1 >= 0.0

    # 2. Random noisy array (high contrast)
    np.random.seed(42)
    noise_arr = np.random.rand(50, 50) * 255.0
    score2 = compute_image_metrics(noise_arr)
    assert score2 > 0.0

    # 3. 3D array check
    arr_3d = np.zeros((50, 50, 3), dtype=np.float64)
    score3 = compute_image_metrics(arr_3d)
    assert score3 >= 0.0
