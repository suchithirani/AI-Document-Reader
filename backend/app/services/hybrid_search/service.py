import re
from collections import Counter


class HybridSearchService:

    def __init__(
        self,
        vector_weight: float = 0.70,
        keyword_weight: float = 0.20,
        semantic_weight: float = 0.10,
        bonus: float = 0.05,
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        self.bonus = bonus

    # =========================================================
    # TOKENIZATION
    # =========================================================

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(
            r"\b[a-zA-Z0-9_]+\b",
            text.lower(),
        )

    # =========================================================
    # QUERY TERMS
    # =========================================================

    def _query_terms(
        self,
        question: str,
    ) -> list[str]:

        stop_words = {
            "give",
            "me",
            "the",
            "a",
            "an",
            "is",
            "are",
            "what",
            "which",
            "show",
            "tell",
            "about",
            "from",
            "of",
            "in",
            "on",
            "for",
            "to",
            "with",
            "important",
            "things",
            "details",
            "information",
            "please",
            "can",
            "you",
            "does",
            "do",
            "describe",
            "explain",
            "list",
            "summarize",
            "summary",
            "main",
            "key",
            "overall",
            "system",
        }

        return [
            word
            for word in self._tokenize(question)
            if word not in stop_words
        ]

    # =========================================================
    # BROAD QUESTION
    # =========================================================

    def _is_broad_question(
        self,
        question: str,
    ) -> bool:

        lowered = question.lower()

        broad_phrases = (
            "important things",
            "important points",
            "key points",
            "main points",
            "main things",
            "overview",
            "summarize",
            "summary",
            "overall",
            "important information",
        )

        return (
            len(self._query_terms(question)) <= 4
            or any(
                phrase in lowered
                for phrase in broad_phrases
            )
        )

    # =========================================================
    # PHRASE SCORE
    # =========================================================

    def _phrase_score(
        self,
        question: str,
        text: str,
    ) -> float:

        terms = self._query_terms(question)

        if len(terms) < 2:
            return 0.0

        normalized_text = " ".join(
            self._tokenize(text)
        )

        normalized_question = " ".join(
            terms
        )

        if normalized_question in normalized_text:
            return 1.0

        for index in range(
            len(terms) - 1
        ):
            phrase = (
                f"{terms[index]} "
                f"{terms[index + 1]}"
            )

            if phrase in normalized_text:
                return 0.6

        return 0.0

    # =========================================================
    # TERM OVERLAP
    # =========================================================

    def _term_overlap_score(
        self,
        question: str,
        text: str,
    ) -> float:

        terms = set(
            self._query_terms(question)
        )

        if not terms:
            return 0.0

        text_terms = set(
            self._tokenize(text)
        )

        matched = sum(
            1
            for term in terms
            if term in text_terms
        )

        return matched / len(terms)

    # =========================================================
    # TERM SPECIFICITY
    # =========================================================

    def _term_specificity(
        self,
        question: str,
        texts: list[str],
    ) -> dict[str, float]:

        terms = set(
            self._query_terms(question)
        )

        if not terms or not texts:
            return {}

        document_frequency = Counter()

        for text in texts:

            text_terms = set(
                self._tokenize(text)
            )

            for term in terms:

                if term in text_terms:
                    document_frequency[term] += 1

        total = len(texts)

        return {
            term: max(
                0.0,
                1.0
                - (
                    document_frequency[term]
                    / total
                ),
            )
            for term in terms
        }

    # =========================================================
    # WEIGHTED OVERLAP
    # =========================================================

    def _weighted_overlap_score(
        self,
        question: str,
        text: str,
        specificity: dict[str, float],
    ) -> float:

        terms = set(
            self._query_terms(question)
        )

        if not terms:
            return 0.0

        text_terms = set(
            self._tokenize(text)
        )

        total_weight = sum(
            specificity.get(
                term,
                1.0,
            )
            for term in terms
        )

        if total_weight <= 0:
            return 0.0

        matched_weight = sum(
            specificity.get(
                term,
                1.0,
            )
            for term in terms
            if term in text_terms
        )

        return (
            matched_weight
            / total_weight
        )

    # =========================================================
    # DOCUMENT QUALITY
    #
    # Generic structural detection.
    # No domain-specific terms.
    # =========================================================

    def _content_quality_score(
        self,
        text: str,
    ) -> float:
        """
        Estimate whether a chunk contains useful document content.

        This is document-type independent.
        It does not assume:
        - report sections
        - invoice fields
        - resume sections
        - contract terminology
        - specific page numbers

        Returns:
            0.0 -> weak/noisy content
            1.0 -> strong content density
        """

        if not text or not text.strip():
            return 0.0

        normalized = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        words = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
            normalized,
        )

        word_count = len(words)

        if word_count == 0:
            return 0.0

        score = 0.0

        # ---------------------------------------------------------
        # 1. Text length
        # ---------------------------------------------------------

        if word_count >= 120:
            score += 0.25
        elif word_count >= 80:
            score += 0.20
        elif word_count >= 40:
            score += 0.12
        elif word_count >= 20:
            score += 0.05

        # ---------------------------------------------------------
        # 2. Alphabetic content ratio
        #
        # Useful text generally contains a reasonable amount of
        # natural language rather than only numbers/symbols.
        # ---------------------------------------------------------

        alphabetic_chars = sum(
            char.isalpha()
            for char in normalized
        )

        total_chars = len(normalized)

        alpha_ratio = (
            alphabetic_chars / total_chars
            if total_chars
            else 0.0
        )

        if alpha_ratio >= 0.70:
            score += 0.15
        elif alpha_ratio >= 0.55:
            score += 0.10
        elif alpha_ratio >= 0.40:
            score += 0.05

        # ---------------------------------------------------------
        # 3. Sentence structure
        # ---------------------------------------------------------

        sentence_count = len(
            re.findall(
                r"[.!?](?:\s|$)",
                normalized,
            )
        )

        if sentence_count >= 4:
            score += 0.15
        elif sentence_count >= 2:
            score += 0.10
        elif sentence_count == 1:
            score += 0.03

        # ---------------------------------------------------------
        # 4. Repetition penalty
        #
        # Headers, footers and extracted navigation text often
        # repeat the same small set of words.
        # ---------------------------------------------------------

        unique_words = len(
            set(
                word.lower()
                for word in words
            )
        )

        vocabulary_ratio = (
            unique_words / word_count
        )

        if vocabulary_ratio >= 0.60:
            score += 0.15
        elif vocabulary_ratio >= 0.45:
            score += 0.10
        elif vocabulary_ratio >= 0.30:
            score += 0.05
        else:
            score -= 0.10

        # ---------------------------------------------------------
        # 5. TOC / navigation structure
        #
        # This is structural rather than document-specific.
        # ---------------------------------------------------------

        dotted_leaders = len(
            re.findall(
                r"\.{4,}",
                text,
            )
        )

        if dotted_leaders >= 3:
            score -= 0.30
        elif dotted_leaders >= 1:
            score -= 0.15

        # ---------------------------------------------------------
        # 6. Excessive line fragmentation
        #
        # OCR/table/navigation chunks can contain many extremely
        # short lines instead of coherent text.
        # ---------------------------------------------------------

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if len(lines) >= 5:

            short_lines = sum(
                1
                for line in lines
                if len(
                    re.findall(
                        r"\b\w+\b",
                        line,
                    )
                ) <= 3
            )

            short_line_ratio = (
                short_lines / len(lines)
            )

            if short_line_ratio >= 0.75:
                score -= 0.20
            elif short_line_ratio >= 0.50:
                score -= 0.10

        return max(
            0.0,
            min(score, 1.0),
        )

    def _content_quality_bonus(
        self,
        text: str,
    ) -> float:

        if not text:
            return 0.0

        lowered = text.lower()

        bonus = 0.0

        # Headings / sections usually indicate actual document content.
        section_patterns = (
            r"\b\d+\.\d+\s+[A-Za-z]",
            r"\bchapter\s+\d+",
            r"\bintroduction\b",
            r"\bobjective\b",
            r"\bpurpose\b",
            r"\bscope\b",
            r"\brequirements?\b",
            r"\bmethodology\b",
            r"\bimplementation\b",
            r"\barchitecture\b",
            r"\bdesign\b",
            r"\btesting\b",
            r"\bconclusion\b",
        )

        for pattern in section_patterns:

            if re.search(
                pattern,
                lowered,
            ):
                bonus += 0.04

        # Actual explanatory text is generally more useful
        # than cover/certificate material.
        word_count = len(
            self._tokenize(text)
        )

        if word_count >= 80:
            bonus += 0.05

        if word_count >= 150:
            bonus += 0.05

        return min(
            bonus,
            0.15,
        )
    # =========================================================
    # MERGE
    # =========================================================

    def merge(
        self,
        vector_results: list,
        keyword_results: list,
        top_k: int = 5,
        question: str = "",
    ):

        merged = {}

        # =====================================================
        # NORMALIZATION
        # =====================================================

        vector_max = max(
            (
                result["score"]
                for result in vector_results
            ),
            default=1.0,
        )

        keyword_max = max(
            (
                result["score"]
                for result in keyword_results
            ),
            default=1.0,
        )

        # =====================================================
        # VECTOR RESULTS
        # =====================================================

        for result in vector_results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            vector_score = (
                result["score"] / vector_max
                if vector_max > 0
                else 0.0
            )

            merged[key] = {
                "chunk": chunk,
                "vector_score": vector_score,
                "keyword_score": 0.0,
                "matched_by_vector": True,
                "matched_by_keyword": False,
            }

        # =====================================================
        # KEYWORD RESULTS
        # =====================================================

        for result in keyword_results:

            chunk = result["chunk"]

            key = (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            )

            keyword_score = (
                result["score"] / keyword_max
                if keyword_max > 0
                else 0.0
            )

            if key in merged:

                merged[key]["keyword_score"] = (
                    keyword_score
                )

                merged[key]["matched_by_keyword"] = True

            else:

                merged[key] = {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "keyword_score": keyword_score,
                    "matched_by_vector": False,
                    "matched_by_keyword": True,
                }

        # =====================================================
        # QUERY ANALYSIS
        # =====================================================

        broad_question = (
            self._is_broad_question(
                question
            )
        )

        candidate_texts = [
            item["chunk"].text
            for item in merged.values()
        ]

        specificity = (
            self._term_specificity(
                question,
                candidate_texts,
            )
        )

        # =====================================================
        # SCORE CANDIDATES
        # =====================================================

        final_results = []

        for item in merged.values():

            chunk = item["chunk"]

            # -------------------------------------------------
            # Phrase matching
            # -------------------------------------------------

            phrase_score = (
                self._phrase_score(
                    question,
                    chunk.text,
                )
            )

            # -------------------------------------------------
            # Term overlap
            # -------------------------------------------------

            overlap_score = (
                self._term_overlap_score(
                    question,
                    chunk.text,
                )
            )

            # -------------------------------------------------
            # Weighted overlap
            # -------------------------------------------------

            weighted_overlap = (
                self._weighted_overlap_score(
                    question,
                    chunk.text,
                    specificity,
                )
            )

            # -------------------------------------------------
            # Semantic lexical signal
            # -------------------------------------------------

            semantic_score = max(
                phrase_score * 0.5,
                weighted_overlap,
            )

            # =================================================
            # BASE HYBRID SCORE
            # =================================================

            score = (
                item["vector_score"]
                * self.vector_weight
            )

            score += (
                item["keyword_score"]
                * self.keyword_weight
            )

            score += (
                semantic_score
                * self.semantic_weight
            )

            # =================================================
            # RETRIEVAL AGREEMENT BONUS
            # =================================================

            if (
                item["matched_by_vector"]
                and item["matched_by_keyword"]
            ):
                score += self.bonus

            # =================================================
            # CONTENT QUALITY
            #
            # Document-type independent.
            #
            # This evaluates whether the chunk contains useful
            # natural-language content rather than assuming
            # a particular document type.
            # =================================================

            content_quality = (
                self._content_quality_score(
                    chunk.text
                )
            )

            # Keep this deliberately small so that
            # content quality cannot overpower semantic
            # relevance.
            content_bonus = (
                content_quality * 0.15
            )

            score += content_bonus

            # =================================================
            # FINAL RESULT
            # =================================================

            final_results.append(
                {
                    "chunk": chunk,
                    "score": score,

                    "vector_score": item[
                        "vector_score"
                    ],

                    "keyword_score": item[
                        "keyword_score"
                    ],

                    "phrase_score": phrase_score,

                    "overlap_score": overlap_score,

                    "weighted_overlap": (
                        weighted_overlap
                    ),

                    "content_quality": (
                        content_quality
                    ),

                    "content_bonus": (
                        content_bonus
                    ),
                }
            )

        # =====================================================
        # SORT
        # =====================================================

        final_results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # =====================================================
        # BROAD QUESTION DIVERSITY
        #
        # Prefer different pages first.
        # =====================================================

        if broad_question:

            diverse_results = []
            used_pages = set()

            for result in final_results:

                chunk = result["chunk"]

                page_key = (
                    chunk.document_id,
                    chunk.page_number,
                )

                if page_key in used_pages:
                    continue

                diverse_results.append(
                    result
                )

                used_pages.add(
                    page_key
                )

                if len(diverse_results) >= top_k:
                    break

            # -------------------------------------------------
            # Fill remaining slots
            # -------------------------------------------------

            selected_keys = {
                (
                    item["chunk"].document_id,
                    item["chunk"].page_number,
                    item["chunk"].chunk_index,
                )
                for item in diverse_results
            }

            for result in final_results:

                key = (
                    result["chunk"].document_id,
                    result["chunk"].page_number,
                    result["chunk"].chunk_index,
                )

                if key in selected_keys:
                    continue

                diverse_results.append(
                    result
                )

                if len(diverse_results) >= top_k:
                    break

            final_results = diverse_results

        # =====================================================
        # DEBUG
        # =====================================================

        print(
            "\n========== HYBRID RESULTS =========="
        )

        print(
            f"Broad question: {broad_question}"
        )

        print(
            f"Candidates: {len(final_results)}"
        )

        for rank, result in enumerate(
            final_results[:15],
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank}. "
                f"page={chunk.page_number}, "
                f"chunk={chunk.chunk_index}, "
                f"final={result['score']:.4f}, "
                f"vector={result['vector_score']:.4f}, "
                f"keyword={result['keyword_score']:.4f}, "
                f"phrase={result['phrase_score']:.4f}, "
                f"overlap={result['overlap_score']:.4f}, "
                f"weighted_overlap="
                f"{result['weighted_overlap']:.4f}, "
                f"content_quality="
                f"{result['content_quality']:.4f}, "
                f"content_bonus="
                f"{result['content_bonus']:.4f}"
            )

            print(
                f"   text={chunk.text[:250]!r}"
            )

        print(
            "====================================\n"
        )

        return final_results[:top_k]