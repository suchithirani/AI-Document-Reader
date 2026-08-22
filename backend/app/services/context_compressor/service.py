class ContextCompressor:

    def compress(
        self,
        results: list,
    ):

        compressed = []
        seen = set()

        for result in results:

            chunk = result["chunk"]

            text = chunk.text.strip()

            key = (chunk.document_id, text[:150])

            if key in seen:
                continue

            seen.add(key)

            compressed.append(result)

        return compressed