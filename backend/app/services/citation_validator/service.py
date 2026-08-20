import re


class CitationValidator:

    CITATION_PATTERN = re.compile(
        r"\[(\d+)\]"
    )

    def validate(
        self,
        answer: str,
        sources: list[dict],
    ) -> str:

        valid_ids = {
            int(source["id"])
            for source in sources
        }

        def replace_invalid(
            match: re.Match,
        ) -> str:

            source_id = int(
                match.group(1)
            )

            if source_id in valid_ids:
                return match.group(0)

            return ""

        return self.CITATION_PATTERN.sub(
            replace_invalid,
            answer,
        )