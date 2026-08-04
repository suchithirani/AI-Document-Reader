import fitz


class PDFOCR:

    def extract_text(
        self,
        file_path: str,
    ) -> list[str]:

        document = fitz.open(file_path)

        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return pages