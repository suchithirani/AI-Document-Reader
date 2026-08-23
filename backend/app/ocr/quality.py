import fitz
import numpy as np
import logging
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_document_quality(file_path: str, extension: str) -> float:
    """
    Computes a readability/quality score (0 to 100) for a document.
    Digital PDFs return 100.0.
    Scanned PDFs and images are analyzed using blur and contrast metrics.
    """
    ext = extension.lower()
    if ext == ".pdf":
        try:
            doc = fitz.open(file_path)
            if len(doc) == 0:
                doc.close()
                return 0.0
            
            # Check the first page
            page = doc[0]
            text = page.get_text("text").strip()
            
            # If the page contains a substantial amount of digital text, it's a high-quality digital PDF
            if len(text) > 100:
                doc.close()
                return 100.0
                
            # Otherwise, render page to compute image quality (scanned PDF)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")
            doc.close()
            return compute_image_metrics(np.array(img, dtype=np.float64))
            
        except Exception as e:
            logger.error("Failed to calculate PDF quality score: %s", e)
            return 50.0 # Safe default
            
    elif ext in (".png", ".jpeg", ".jpg", ".webp", ".tiff", ".bmp"):
        try:
            img = Image.open(file_path).convert("L")
            return compute_image_metrics(np.array(img, dtype=np.float64))
        except Exception as e:
            logger.error("Failed to calculate Image quality score: %s", e)
            return 50.0
            
    return 100.0 # Default for other text formats

def compute_image_metrics(gray: np.ndarray) -> float:
    """
    Computes quality metrics using Laplacian variance (blur) and standard deviation (contrast).
    Returns a combined score from 0.0 to 100.0.
    """
    if gray.ndim > 2:
        gray = gray.mean(axis=2)
        
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 50.0

    # 1. Blur score (Discrete 2D Laplacian operator variance)
    # laplacian kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    lap = (gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:]) - 4.0 * gray[1:-1, 1:-1]
    variance = float(lap.var())
    blur_score = min(100.0, (variance / 80.0) * 100.0)
    
    # 2. Contrast score (Standard deviation)
    std_dev = float(gray.std())
    contrast_score = min(100.0, (std_dev / 45.0) * 100.0)
    
    # 3. Combine scores (weighted average: 60% blur, 40% contrast)
    combined = (blur_score * 0.6) + (contrast_score * 0.4)
    return round(combined, 2)
