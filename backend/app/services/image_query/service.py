

class ImageQueryService:

    IMAGE_KEYWORDS = {
        # English
        "image",
        "images",
        "picture",
        "pictures",
        "photo",
        "photos",
        "figure",
        "figures",
        "diagram",
        "diagrams",
        "chart",
        "charts",
        "graph",
        "graphs",
        "screenshot",
        "screenshots",
        "visual",
        "visuals",

        # Hindi / Hinglish
        "tasveer",
        "tasveere",
        "tasvir",
        "tasveerein",

        # Gujarati / Hinglish
        "chitra",
    }

    PAGE_KEYWORDS = {
        # English
        "page",
        "pages",

        # Hindi / Hinglish
        "panna",
        "page",

        # Gujarati / Hinglish
        "prushth",
        "panu",
    }

    def requires_images(
        self,
        question: str,
    ) -> bool:

        question = question.lower()

        # Explicit image/visual request
        if any(
            keyword in question
            for keyword in self.IMAGE_KEYWORDS
        ):
            return True

        # Page-specific questions are handled
        # separately by SearchService because we
        # need to know whether those pages contain images.
        return False

    def has_page_reference(
        self,
        question: str,
    ) -> bool:

        question = question.lower()

        return any(
            keyword in question
            for keyword in self.PAGE_KEYWORDS
        )
