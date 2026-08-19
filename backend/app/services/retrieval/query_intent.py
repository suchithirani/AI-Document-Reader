import re
from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    """
    Generic query intents.

    These are intentionally document-agnostic.
    They should work for reports, invoices, resumes,
    manuals, research papers, contracts, etc.
    """

    BROAD = "broad"
    SPECIFIC = "specific"
    SECTION = "section"
    ENTITY = "entity"
    VISUAL = "visual"
    GENERAL = "general"


@dataclass(frozen=True)
class QueryAnalysis:
    """
    Result of analysing a user's question.
    """

    intent: QueryIntent

    is_broad: bool = False

    specific_page: int | None = None

    requires_vision: bool = False

    confidence: float = 0.0


class QueryIntentAnalyzer:
    """
    Generic query analyzer.

    Responsibilities:
    - detect broad questions
    - detect specific questions
    - detect section/topic questions
    - detect entity-oriented questions
    - detect visual questions
    - detect explicit page references

    It does NOT know what type of document it is analysing.
    """

    PAGE_PATTERNS = (
        r"\bpage\s+(\d+)\b",
        r"\bpage\s*number\s*(\d+)\b",
        r"\bp\.?\s*(\d+)\b",
    )

    VISUAL_TERMS = (
        "image",
        "figure",
        "diagram",
        "chart",
        "graph",
        "table",
        "screenshot",
        "photo",
        "picture",
        "visual",
        "illustration",
        "shown",
        "depicted",
    )

    BROAD_TERMS = (
        "important things",
        "important points",
        "key points",
        "main points",
        "main things",
        "overall",
        "in general",
        "overview",
        "summarize",
        "summary",
        "what is this document about",
        "what is this system about",
        "explain the document",
        "explain the system",
    )

    SECTION_TERMS = (
        "section",
        "chapter",
        "requirements",
        "features",
        "functionalities",
        "objectives",
        "scope",
        "methodology",
        "architecture",
        "design",
        "testing",
        "conclusion",
        "references",
        "enhancement",
        "introduction",
    )

    ENTITY_PATTERNS = (
        r"\bwho\b",
        r"\bwhose\b",
        r"\bwhich person\b",
        r"\bwhich people\b",
        r"\bwhat person\b",
        r"\bwhat company\b",
        r"\bwhat organization\b",
        r"\bwhat product\b",
        r"\bwhat item\b",
        r"\bwhat name\b",
    )

    def analyze(
        self,
        question: str,
    ) -> QueryAnalysis:

        normalized = self._normalize(
            question
        )

        # ---------------------------------------------
        # Page reference
        # ---------------------------------------------

        page_number = self._extract_page(
            normalized
        )

        # ---------------------------------------------
        # Visual question
        # ---------------------------------------------

        requires_vision = self._contains_visual_terms(
            normalized
        )

        if requires_vision:

            return QueryAnalysis(
                intent=QueryIntent.VISUAL,
                is_broad=False,
                specific_page=page_number,
                requires_vision=True,
                confidence=0.95,
            )

        # ---------------------------------------------
        # Explicit page without visual wording
        # ---------------------------------------------

        if page_number is not None:

            return QueryAnalysis(
                intent=QueryIntent.SPECIFIC,
                is_broad=False,
                specific_page=page_number,
                requires_vision=False,
                confidence=0.95,
            )

        # ---------------------------------------------
        # Broad
        # ---------------------------------------------

        if self._contains_any(
            normalized,
            self.BROAD_TERMS,
        ):

            return QueryAnalysis(
                intent=QueryIntent.BROAD,
                is_broad=True,
                confidence=0.90,
            )

        # ---------------------------------------------
        # Section / topic
        # ---------------------------------------------

        if self._contains_any(
            normalized,
            self.SECTION_TERMS,
        ):

            return QueryAnalysis(
                intent=QueryIntent.SECTION,
                is_broad=False,
                confidence=0.85,
            )

        # ---------------------------------------------
        # Entity
        # ---------------------------------------------

        if self._matches_entity_pattern(
            normalized
        ):

            return QueryAnalysis(
                intent=QueryIntent.ENTITY,
                is_broad=False,
                confidence=0.85,
            )

        # ---------------------------------------------
        # Short focused question
        # ---------------------------------------------

        if self._looks_specific(
            normalized
        ):

            return QueryAnalysis(
                intent=QueryIntent.SPECIFIC,
                is_broad=False,
                confidence=0.65,
            )

        # ---------------------------------------------
        # Fallback
        # ---------------------------------------------

        return QueryAnalysis(
            intent=QueryIntent.GENERAL,
            is_broad=False,
            confidence=0.50,
        )

    # =================================================
    # Helpers
    # =================================================

    @staticmethod
    def _normalize(
        question: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            question.lower().strip(),
        )

    @classmethod
    def _extract_page(
        cls,
        question: str,
    ) -> int | None:

        for pattern in cls.PAGE_PATTERNS:

            match = re.search(
                pattern,
                question,
            )

            if match:
                return int(
                    match.group(1)
                )

        return None

    @staticmethod
    def _contains_any(
        question: str,
        terms: tuple[str, ...],
    ) -> bool:

        return any(
            term in question
            for term in terms
        )

    @classmethod
    def _contains_visual_terms(
        cls,
        question: str,
    ) -> bool:

        return cls._contains_any(
            question,
            cls.VISUAL_TERMS,
        )

    @classmethod
    def _matches_entity_pattern(
        cls,
        question: str,
    ) -> bool:

        return any(
            re.search(
                pattern,
                question,
            )
            for pattern in cls.ENTITY_PATTERNS
        )

    @staticmethod
    def _looks_specific(
        question: str,
    ) -> bool:

        words = question.split()

        return len(words) <= 15