from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings

# Global MongoDB client and database
client: AsyncMongoClient | None = None
database: AsyncDatabase | None = None


async def connect_to_mongodb() -> None:
    """
    Create MongoDB connection.
    """
    global client, database

    client = AsyncMongoClient(
        settings.MONGODB_URI,
        maxPoolSize=50,
        minPoolSize=0,
        maxIdleTimeMS=45000,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=30000,
        retryWrites=True,
    )
    database = client[settings.DATABASE_NAME]

    print("✅ Connected to MongoDB")


async def close_mongodb_connection() -> None:
    """
    Close MongoDB connection.
    """
    global client

    if client is not None:
        await client.close()
        print("🔴 MongoDB connection closed")


def get_database() -> AsyncDatabase:
    """
    Return the database instance.
    """
    if database is None:
        raise RuntimeError("MongoDB is not connected.")

    return database
