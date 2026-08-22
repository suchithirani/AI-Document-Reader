import fitz
import re
import numpy as np
import logging
from app.common.exceptions.document import (
    OCRException,
)

logger = logging.getLogger(__name__)

class PDFOCR:

    def __init__(self):
        self._easy_ocr = None
        import threading
        self._easy_ocr_lock = threading.Lock()

    def _get_easy_ocr(self):
        with self._easy_ocr_lock:
            if self._easy_ocr is None:
                logger.info("Initializing EasyOCR (this may take a moment on first load)...")
                import easyocr
                # We support English. (Numbers and english letters will be extracted perfectly)
                self._easy_ocr = easyocr.Reader(['en'], gpu=False)
            return self._easy_ocr

    def _table_to_markdown(self, table_data: list[list[str]]) -> str:
        if not table_data or not table_data[0]:
            return ""

        markdown = []
        # Header
        headers = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in table_data[0]]
        markdown.append("| " + " | ".join(headers) + " |")
        
        # Separator
        separator = ["---"] * len(headers)
        markdown.append("| " + " | ".join(separator) + " |")
        
        # Rows
        for row in table_data[1:]:
            cells = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
            cells.extend([""] * (len(headers) - len(cells)))
            markdown.append("| " + " | ".join(cells[:len(headers)]) + " |")
            
        return "\n".join(markdown)

    def extract_text(
        self,
        file_path: str,
    ) -> list[str]:
        try:
            document = fitz.open(file_path)
            num_pages = len(document)
            document.close()

            import concurrent.futures
            
            # Bound parallel workers to max 4 to preserve CPU and memory
            max_workers = min(num_pages, 4)
            pages = [None] * num_pages

            logger.info("Starting parallel text extraction for %s using %d workers", file_path, max_workers)

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_page_parallel, file_path, page_num): page_num
                    for page_num in range(num_pages)
                }

                for future in concurrent.futures.as_completed(futures):
                    page_num = futures[future]
                    try:
                        pages[page_num] = future.result()
                    except Exception as e:
                        logger.error("Error processing page %d: %s", page_num, e)
                        raise

            return pages

        except Exception as exception:
            raise OCRException(
                str(exception)
            ) from exception

    def _process_page_parallel(self, file_path: str, page_number: int) -> str:
        document = fitz.open(file_path)
        try:
            page = document[page_number]
            # 1. Digital Table Extraction (Layout-Aware)
            tables = page.find_tables()
            table_bboxes = []
            extracted_items = []

            for table in tables:
                table_bboxes.append(table.bbox)
                table_data = table.extract()
                md_table = self._table_to_markdown(table_data)
                if md_table:
                    extracted_items.append({
                        'y': table.bbox[1],
                        'text': md_table
                    })

            # 2. Digital Text Extraction
            blocks = page.get_text("blocks")

            for block in blocks:
                block_rect = fitz.Rect(block[:4])
                
                # Check if this block is inside any extracted table
                in_table = False
                for bbox in table_bboxes:
                    table_rect = fitz.Rect(bbox)
                    if table_rect.intersects(block_rect):
                        intersection = table_rect.intersect(block_rect)
                        block_area = block_rect.get_area()
                        if block_area > 0 and (intersection.get_area() / block_area) > 0.5:
                            in_table = True
                            break
                
                if in_table:
                    continue
                    
                text = block[4].strip()
                if not text:
                    continue
                    
                text = self._clean_text(text)
                if text:
                    extracted_items.append({
                        'y': block[1],
                        'text': text
                    })

            # Sort all extracted items (tables and text blocks) vertically
            extracted_items.sort(key=lambda item: item['y'])
            
            page_text = [item['text'] for item in extracted_items]
            combined_text = "\n\n".join(page_text).strip()

            # 3. Hybrid Fallback: Scanned PDF / Image Detection
            if len(combined_text) < 20:
                logger.info("Page %d of %s yielded little/no digital text. Falling back to EasyOCR.", page_number, file_path)
                combined_text = self._extract_with_easyocr(page)

            return combined_text
        finally:
            document.close()

    def _extract_with_easyocr(self, page) -> str:
        """
        Renders the PDF page to an image and uses EasyOCR's vision model to read the text.
        """
        # Render at 2x zoom for better OCR accuracy (around 150-200 DPI depending on original size)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to numpy array (H, W, C) for EasyOCR
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        if pix.n == 4:
            import cv2
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        ocr = self._get_easy_ocr()
        # EasyOCR returns a list of tuples: (bounding_box, text, confidence)
        result = ocr.readtext(img)

        if not result:
            return ""

        # Extract text blocks
        lines = []
        for line in result:
            text = line[1]
            lines.append(text)

        return self._clean_text("\n\n".join(lines))

    def _clean_text(
        self,
        text: str,
    ) -> str:

        text = text.replace(
            "\r",
            "",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()