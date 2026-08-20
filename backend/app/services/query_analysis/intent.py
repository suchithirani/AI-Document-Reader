import re

from app.common.constants import QueryIntent


class QueryIntentDetector:

    def detect(
        self,
        question: str,
    ) -> QueryIntent:

        normalized = question.lower().strip()

        if self._is_toc(normalized):
            return QueryIntent.TOC
        
        if self._is_comparison(normalized):
            return QueryIntent.COMPARISON

        if self._is_summary(normalized):
            return QueryIntent.SUMMARY

        if self._is_extraction(normalized):
            return QueryIntent.EXTRACTION

        if self._is_explanation(normalized):
            return QueryIntent.EXPLANATION

        if self._is_factual(normalized):
            return QueryIntent.FACTUAL

        return QueryIntent.GENERAL

    def _is_toc(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"\btable of contents\b",
            r"\bcontents\b",
            r"\bchapter list\b",
            r"\bchapter overview\b",
            r"\bsection list\b",
            r"\bsection overview\b",
            r"list of contents\b",
            r"list the contents\b",
            r"document contents\b",
            r"toc\b",
            r"chapter list\b",
            r"list of chapters\b",
            r"list all chapters\b",
            r"document structure\b",
        )

        return self._matches(
            question,
            patterns,
        )

    def _is_comparison(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"\bcompare\b",
            r"\bcomparison\b",
            r"\bdifference between\b",
            r"\bdifferences between\b",
            r"\bsimilarities\b",
            r"\bsimilar\b",
            r"\bversus\b",
            r"\bvs\.?\b",
        )

        return self._matches(
            question,
            patterns,
        )

    def _is_summary(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"\bsummarize\b",
            r"\bsummary\b",
            r"\boverview\b",
            r"\bbriefly\b",
            r"\bmain points\b",
            r"\bkey points\b",
            r"\bimportant points\b",
            r"\bimportant things\b",
        )

        return self._matches(
            question,
            patterns,
        )

    def _is_extraction(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"\blist\b",
            r"\bextract\b",
            r"\bfind all\b",
            r"\bwhat are\b",
            r"\bwhich are\b",
        )

        return self._matches(
            question,
            patterns,
        )

    def _is_explanation(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"\bexplain\b",
            r"\bhow does\b",
            r"\bhow do\b",
            r"\bwhy does\b",
            r"\bwhy do\b",
            r"\bdescribe\b",
            r"\bclarify\b",
        )

        return self._matches(
            question,
            patterns,
        )

    def _is_factual(
        self,
        question: str,
    ) -> bool:

        patterns = (
            r"^what\b",
            r"^who\b",
            r"^when\b",
            r"^where\b",
            r"^which\b",
            r"^is\b",
            r"^are\b",
            r"^does\b",
            r"^do\b",
            r"^can\b",
        )

        return self._matches(
            question,
            patterns,
        )

    @staticmethod
    def _matches(
        question: str,
        patterns: tuple[str, ...],
    ) -> bool:

        return any(
            re.search(
                pattern,
                question,
            )
            for pattern in patterns
        )