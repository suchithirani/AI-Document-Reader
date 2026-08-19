from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageOps,
)
from pathlib import Path
from app.common.exceptions.document import (
    OCRException,
)
import pytesseract


class ImageOCR:


    def extract_text(
        self,
        source: str | Path | Image.Image,
    ) -> list[str]:

        try:

            if isinstance(source, Image.Image):
                image = source.copy()

            else:
                image = Image.open(source)

        except Exception as exception:
            raise OCRException(
                str(exception)
            ) from exception

        image = self._preprocess(image)

        text = pytesseract.image_to_string(
            image,
            config="--oem 3 --psm 6",
        )

        return [text]

    def _preprocess(
        self,
        image: Image.Image,
    ) -> Image.Image:

        image = image.convert("L")

        image = ImageOps.autocontrast(image)

        image = image.resize(
            (
                image.width * 2,
                image.height * 2,
            ),
            Image.Resampling.LANCZOS,
        )

        image = image.filter(
            ImageFilter.MedianFilter()
        )

        image = image.filter(
            ImageFilter.SHARPEN
        )

        image = ImageEnhance.Contrast(
            image
        ).enhance(2.0)

        image = image.point(
            lambda pixel: (
                255 if pixel > 160 else 0
            )
        )

        return image