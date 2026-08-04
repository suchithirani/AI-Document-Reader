from PIL import Image
import pytesseract


class ImageOCR:

    def extract_text(
        self,
        file_path: str,
    ) -> list[str]:

        image = Image.open(file_path)

        text = pytesseract.image_to_string(image)

        return [text]