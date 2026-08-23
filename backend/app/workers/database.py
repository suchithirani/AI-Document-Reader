from pymongo import AsyncMongoClient

from app.core.config import settings


_client: AsyncMongoClient | None = None


async def get_worker_database():

    global _client

    if _client is None:

        _client = AsyncMongoClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=0,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            retryWrites=True,
        )

        await _client.aconnect()

    return (
        _client,
        _client[settings.DATABASE_NAME],
    )


async def close_worker_database():

    global _client

    if _client is not None:

        await _client.close()

        _client = None