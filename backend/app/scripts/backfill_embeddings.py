# scripts/backfill_embeddings.py

import asyncio

from app.modules.document_chunks.repository import DocumentChunkRepository
from app.services.embedding.gemini import GeminiEmbedding
from app.workers.database import get_worker_database

BATCH_SIZE = 25
BATCH_DELAY_SECONDS = 65


async def main():

    _, db = await get_worker_database()

    repository = DocumentChunkRepository(db)
    embedding_service = GeminiEmbedding()

    chunks = await repository.get_many(
        filters={
            "embedding": None,
        },
        skip=0,
        limit=100000,
        sort=[
            ("document_id", 1),
            ("page_number", 1),
            ("chunk_index", 1),
        ],
    )

    print(f"Missing embeddings: {len(chunks)}")

    for start in range(
        0,
        len(chunks),
        BATCH_SIZE,
    ):

        batch = chunks[
            start:start + BATCH_SIZE
        ]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        print(
            f"Embedding {start + 1}-"
            f"{start + len(batch)} "
            f"of {len(chunks)}"
        )

        embeddings = (
            await embedding_service.create_embeddings(
                texts
            )
        )

        if len(embeddings) != len(batch):
            raise RuntimeError(
                f"Expected {len(batch)} embeddings, "
                f"got {len(embeddings)}"
            )

        for chunk, embedding in zip(
            batch,
            embeddings,
        ):

            if not embedding:
                raise RuntimeError(
                    f"Empty embedding: "
                    f"page={chunk['page_number']} "
                    f"chunk={chunk['chunk_index']}"
                )

            result = await repository.update_embedding(
                document_id=chunk["document_id"],
                page_number=chunk["page_number"],
                chunk_index=chunk["chunk_index"],
                embedding=embedding,
            )

            if result is None:
                raise RuntimeError(
                    f"Failed to update embedding: "
                    f"page={chunk['page_number']} "
                    f"chunk={chunk['chunk_index']}"
                )

                print(
                    f"Batch completed: "
                    f"{start + 1}-{start + len(batch)}"
                )

                if start + len(batch) < len(chunks):
                    print(
                        f"Waiting {BATCH_DELAY_SECONDS}s "
                        "before next batch..."
                    )
                    await asyncio.sleep(
                        BATCH_DELAY_SECONDS
                    )



if __name__ == "__main__":
    asyncio.run(main())
