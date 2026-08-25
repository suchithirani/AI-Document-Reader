import logging
import re

import fitz
import pytesseract
from PIL import Image, ImageOps

from app.common.exceptions.document import (
    OCRException,
)

logger = logging.getLogger(__name__)

class PDFOCR:

    def __init__(self):
        pass

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
                logger.info("Page %d of %s yielded little/no digital text. Falling back to OCR.", page_number, file_path)
                combined_text = self._extract_with_ocr(page)

            return combined_text
        finally:
            document.close()

    def _extract_with_ocr(self, page) -> str:
        """
        Renders the PDF page to an image and uses Tesseract OCR to read the text.
        """
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_l = ImageOps.autocontrast(img.convert("L"))

        text = pytesseract.image_to_string(
            img_l,
            config="--oem 3 --psm 6",
        )

        return self._clean_text(text)

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
