from app.ocr.image import ImageOCR
from app.ocr.pdf import PDFOCR


class OCRFactory:

    @staticmethod
    def get_engine(
        extension: str,
    ):

        extension = extension.lower()

        if extension == ".pdf":
            return PDFOCR()

        if extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".tiff",
        }:
            return ImageOCR()

        raise ValueError(
            "Unsupported file type."
        )