import fitz

from app.common.exceptions.document import (
    OCRException,
)


class PDFImageExtractor:

    def extract_images(
        self,
        file_path: str,
    ) -> list[dict]:

        document = None

        try:

            document = fitz.open(file_path)

            images = []

            for page_number, page in enumerate(
                document,
                start=1,
            ):

                page_images = page.get_images(
                    full=True
                )

                for image_index, image_info in enumerate(
                    page_images,
                    start=1,
                ):

                    xref = image_info[0]

                    image_data = document.extract_image(
                        xref
                    )

                    if not image_data:
                        continue

                    images.append(
                        {
                            "page_number": page_number,
                            "image_index": image_index,
                            "extension": image_data[
                                "ext"
                            ],
                            "image_bytes": image_data[
                                "image"
                            ],
                            "width": image_data[
                                "width"
                            ],
                            "height": image_data[
                                "height"
                            ],
                        }
                    )

            return images

        except Exception as exception:

            raise OCRException(
                str(exception)
            ) from exception

        finally:

            if document is not None:
                document.close()