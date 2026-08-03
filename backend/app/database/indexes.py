from pymongo import ASCENDING

from app.common.constants import CollectionName


async def create_indexes(db):
    refresh_tokens = db[CollectionName.REFRESH_TOKENS.value]

    await refresh_tokens.create_index(
        [("token_hash", ASCENDING)],
        unique=True,
    )

    await refresh_tokens.create_index(
        [("user_id", ASCENDING)],
    )

    await refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
    )