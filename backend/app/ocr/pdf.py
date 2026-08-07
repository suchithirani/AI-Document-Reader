import fitz
import re
from app.common.exceptions.document import (
    OCRException,
)

class PDFOCR:

    def extract_text(
        self,
        file_path: str,
    ) -> list[str]:
        try:
            document = fitz.open(file_path)

            pages = []

            for page in document:

                blocks = page.get_text("blocks")

                blocks.sort(
                    key=lambda block: (
                        round(block[1], 1),
                        round(block[0], 1),
                    )
                )

                page_text = []

                for block in blocks:

                    text = block[4].strip()

                    if not text:
                        continue

                    text = self._clean_text(text)

                    page_text.append(text)

                pages.append("\n\n".join(page_text))

            document.close()

            return pages

        except Exception as exception:

            raise OCRException(
                str(exception)
            ) from exception

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