import re


class ChunkingService:

    def split_text(
        self,
        text: str,
        chunk_size: int = 800,
        overlap_sentences: int = 2,
    ) -> list[str]:

        text = self._clean_text(text)

        if not text:
            return []

        paragraphs = self._split_paragraphs(text)

        sentences = []

        for paragraph in paragraphs:
            sentences.extend(
                self._split_sentences(paragraph)
            )

        chunks = self._pack_chunks(
            sentences,
            chunk_size,
        )

        chunks = self._add_overlap(
            chunks,
            overlap_sentences,
        )

        return chunks

    def _clean_text(
        self,
        text: str,
    ) -> str:

        text = text.replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    def _split_paragraphs(
        self,
        text: str,
    ) -> list[str]:

        paragraphs = re.split(
            r"\n\s*\n",
            text,
        )

        return [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    def _split_sentences(
        self,
        text: str,
    ) -> list[str]:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _pack_chunks(
        self,
        sentences: list[str],
        chunk_size: int,
    ) -> list[str]:

        chunks = []

        current = ""

        for sentence in sentences:

            if (
                len(current)
                + len(sentence)
                + 1
                <= chunk_size
            ):

                current += sentence + " "

            else:

                if current.strip():
                    chunks.append(
                        current.strip()
                    )

                current = sentence + " "

        if current.strip():
            chunks.append(
                current.strip()
            )

        return chunks

    def _add_overlap(
        self,
        chunks: list[str],
        overlap_sentences: int,
    ) -> list[str]:

        if overlap_sentences <= 0:
            return chunks

        overlapped = []

        previous = []

        for chunk in chunks:

            sentences = self._split_sentences(
                chunk
            )

            combined = (
                previous
                + sentences
            )

            overlapped.append(
                " ".join(combined)
            )

            previous = sentences[
                -overlap_sentences:
            ]

        return overlapped