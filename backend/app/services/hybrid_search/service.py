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

    def _tokenize(
        self,
        text: str,
    ) -> list[str]:

        return re.findall(
            r"\b[a-zA-Z0-9_]+\b",
            text.lower(),
        )

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

    def _content_quality_score(
        self,
        text: str,
    ) -> float:
        """
        Estimate generic text quality without assuming
        a particular document type.
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

        if word_count >= 120:
            score += 0.25
        elif word_count >= 80:
            score += 0.20
        elif word_count >= 40:
            score += 0.12
        elif word_count >= 20:
            score += 0.05

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

        unique_words = len({word.lower() for word in words})

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

    def merge(
        self,
        vector_results: list,
        keyword_results: list,
        top_k: int = 5,
        question: str = "",
    ):

        merged = {}

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

        final_results = []

        for item in merged.values():

            chunk = item["chunk"]

            phrase_score = (
                self._phrase_score(
                    question,
                    chunk.text,
                )
            )

            overlap_score = (
                self._term_overlap_score(
                    question,
                    chunk.text,
                )
            )

            weighted_overlap = (
                self._weighted_overlap_score(
                    question,
                    chunk.text,
                    specificity,
                )
            )

            semantic_score = max(
                phrase_score * 0.5,
                weighted_overlap,
            )

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

            if (
                item["matched_by_vector"]
                and item["matched_by_keyword"]
            ):
                score += self.bonus

            content_quality = (
                self._content_quality_score(
                    chunk.text
                )
            )

            content_bonus = (
                content_quality * 0.15
            )

            score += content_bonus

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

        final_results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

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

                used_pages.add(page_key)

                if len(diverse_results) >= top_k:
                    break

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

        return final_results[:top_k]
