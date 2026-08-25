import re


class PageQueryService:

    PAGE_PATTERNS = [
        # ---------------------------------
        # English / Hinglish
        # ---------------------------------

        r"\bpages?\s*(?:numbers?|nos?\.?|#)?\s*"
        r"(\d+(?:\s*[,/&-]\s*\d+)*)",

        r"\bon\s+pages?\s*"
        r"(\d+(?:\s*[,/&-]\s*\d+)*)",

        r"\bfrom\s+pages?\s*"
        r"(\d+(?:\s*[,/&-]\s*\d+)*)",

        # ---------------------------------
        # Hindi / Hinglish
        # ---------------------------------

        r"\bपेज\s*(?:नंबर|नं\.?)?\s*"
        r"(\d+(?:\s*[,/&-]\s*\d+)*)",

        # ---------------------------------
        # Gujarati
        # ---------------------------------

        r"\bપેજ\s*(?:નંબર|નં\.?)?\s*"
        r"(\d+(?:\s*[,/&-]\s*\d+)*)",
    ]

    def extract_page_numbers(
        self,
        question: str,
    ) -> list[int]:

        pages = set()

        for pattern in self.PAGE_PATTERNS:

            matches = re.findall(
                pattern,
                question,
                flags=re.IGNORECASE,
            )

            for match in matches:

                numbers = re.findall(
                    r"\d+",
                    match,
                )

                for number in numbers:

                    page = int(number)

                    if page > 0:
                        pages.add(page)

        return sorted(pages)

    def has_explicit_page(
        self,
        question: str,
    ) -> bool:

        return bool(
            self.extract_page_numbers(
                question
            )
        )
