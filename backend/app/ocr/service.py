from app.ocr.factory import OCRFactory


class OCRService:

    def extract_text(
        self,
        file_path: str,
        extension: str,
    ) -> list[str]:

        engine = OCRFactory.get_engine(
            extension
        )

        return engine.extract_text(
            file_path
        )
