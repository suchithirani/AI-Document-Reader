import asyncio

from app.services.embedding.gemini import GeminiEmbedding


async def main():
    service = GeminiEmbedding()

    embedding = await service.create_embedding(
        "Hello World"
    )

    print(f"Type: {type(embedding)}")
    print(f"Length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


asyncio.run(main())