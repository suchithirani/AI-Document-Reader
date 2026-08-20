import re

from app.services.query_analysis.intent import QueryIntentDetector
from app.services.query_analysis.models import QueryAnalysis
from app.common.constants import QueryIntent, QueryScope


class QueryAnalyzer:

    def __init__(self):
        self.intent_detector = QueryIntentDetector()

    def analyze(self, question: str) -> QueryAnalysis:

        normalized = self._normalize(question)

        intent = self.intent_detector.detect(normalized)

        page_numbers = self._extract_pages(normalized)

        requires_visual = self._requires_visual_context(
            normalized,
            intent,
        )

        is_broad = self._is_broad(
            normalized,
            intent,
            page_numbers,
        )

        scope = self._determine_scope(
            page_numbers,
            is_broad,
        )

        query_terms = self._extract_query_terms(
            normalized
        )

        retrieval_top_k = self._get_retrieval_top_k(
            intent=intent,
            is_broad=is_broad,
            scope=scope,
        )

        return QueryAnalysis(
            intent=intent,
            scope=scope,
            is_broad=is_broad,
            requires_visual=requires_visual,
            page_numbers=page_numbers,
            query_terms=query_terms,
            retrieval_top_k=retrieval_top_k,
        )

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, question: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            question.strip().lower(),
        )

    # ---------------------------------------------------------
    # PAGE EXTRACTION
    # ---------------------------------------------------------

    def _extract_pages(
        self,
        question: str,
    ) -> list[int]:

        patterns = (
            r"\bpages?\s+(?:no\.?|number\s*)?(\d+)\b",
            r"\bon\s+page\s+(\d+)\b",
            r"\bpage\s+(\d+)\b",

            # Hinglish
            r"\bpage\s+(\d+)\s+(?:par|pe|mein|me)\b",
            r"\b(\d+)\s+(?:page|par|pe|mein|me)\b",

            # Gujarati
            r"\bpage\s+(\d+)\s+(?:ma|માં|પર)\b",
            r"\b(\d+)\s+(?:page|ma|માં|પર)\b",
        )

        pages = set()

        for pattern in patterns:
            for match in re.findall(pattern, question):
                pages.add(int(match))

        return sorted(pages)

    # ---------------------------------------------------------
    # VISUAL CONTEXT
    # ---------------------------------------------------------

    def _requires_visual_context(
        self,
        question: str,
        intent: QueryIntent,
    ) -> bool:

        # TOC is TEXT retrieval.
        if intent == QueryIntent.TOC:
            return False

        visual_terms = (
            "image",
            "picture",
            "photo",
            "photograph",
            "diagram",
            "chart",
            "graph",
            "figure",
            "table",
            "illustration",
            "screenshot",
            "visual",
            "shown",
            "displayed",
        )

        return any(
            term in question
            for term in visual_terms
        )

    # ---------------------------------------------------------
    # BROAD QUESTION
    # ---------------------------------------------------------

    def _is_broad(
        self,
        question: str,
        intent: QueryIntent,
        page_numbers: list[int],
    ) -> bool:

        if page_numbers:
            return False

        # TOC is NOT a broad semantic search.
        if intent == QueryIntent.TOC:
            return False

        if intent == QueryIntent.SUMMARY:
            return True

        if intent == QueryIntent.GENERAL:
            return True

        meaningful_terms = self._extract_query_terms(
            question
        )

        return len(meaningful_terms) <= 4

    # ---------------------------------------------------------
    # SCOPE
    # ---------------------------------------------------------

    def _determine_scope(
        self,
        page_numbers: list[int],
        is_broad: bool,
    ) -> QueryScope:

        if page_numbers:
            return QueryScope.PAGE

        if is_broad:
            return QueryScope.GLOBAL

        return QueryScope.TARGETED

    # ---------------------------------------------------------
    # QUERY TERMS
    # ---------------------------------------------------------

    def _extract_query_terms(
        self,
        question: str,
    ) -> list[str]:

        stop_words = {
            "a", "an", "the",
            "is", "are", "was", "were",
            "what", "which", "who",
            "when", "where", "why", "how",
            "does", "do", "did",
            "can", "could", "would", "should", "will",
            "about", "from", "with", "for",
            "this", "that", "these", "those",
            "me", "my",
            "please",
            "tell", "give",
            "explain", "describe",
            "list", "show",
        }

        terms = re.findall(
            r"\b[a-zA-Z0-9_]+\b",
            question,
        )

        return [
            term
            for term in terms
            if term not in stop_words
        ]

    # ---------------------------------------------------------
    # RETRIEVAL TOP K
    # ---------------------------------------------------------

    def _get_retrieval_top_k(
        self,
        intent: QueryIntent,
        is_broad: bool,
        scope: QueryScope,
    ) -> int:

        # TOC should retrieve very few candidate chunks.
        if intent == QueryIntent.TOC:
            return 3

        if scope == QueryScope.PAGE:
            return 10

        if scope == QueryScope.GLOBAL:
            return 15

        if is_broad:
            return 15

        if intent == QueryIntent.COMPARISON:
            return 12

        return 10