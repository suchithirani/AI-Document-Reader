from pymongo import ASCENDING

from app.common.constants import CollectionName


async def create_user_indexes(db):
    users = db[CollectionName.USERS.value]

    await users.create_index(
        [("email", ASCENDING)],
        unique=True,
    )

    await users.create_index(
        [("phone_number", ASCENDING)],
        unique=True,
        sparse=True,
    )

    await users.create_index(
        [("google_id", ASCENDING)],
        sparse=True,
    )

async def create_refresh_token_indexes(db):
    refresh_tokens = db[
        CollectionName.REFRESH_TOKENS.value
    ]

    await refresh_tokens.create_index(
        [("token_hash", ASCENDING)],
        unique=True,
        sparse=True,
    )

    await refresh_tokens.create_index(
        [("user_id", ASCENDING)],
    )

    await refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
    )

async def create_request_log_indexes(db):
    request_logs = db[
        CollectionName.REQUEST_LOGS.value
    ]

    await request_logs.create_index(
        [("request_id", ASCENDING)],
        unique=True,
    )

    await request_logs.create_index(
        [("timestamp", ASCENDING)],
    )

    await request_logs.create_index(
        [("user_id", ASCENDING)],
    )

    await request_logs.create_index(
        [("path", ASCENDING)],
    )

    await request_logs.create_index(
        [("status_code", ASCENDING)],
    )

async def create_audit_log_indexes(db):

    audit_logs = db[
        CollectionName.AUDIT_LOGS.value
    ]

    await audit_logs.create_index(
        [("user_id", ASCENDING)]
    )

    await audit_logs.create_index(
        [("action", ASCENDING)]
    )

    await audit_logs.create_index(
        [("resource", ASCENDING)]
    )

    await audit_logs.create_index(
        [("created_at", ASCENDING)]
    )

async def create_document_indexes(db):
    documents = db[
        CollectionName.DOCUMENTS.value
    ]

    await documents.create_index(
        "owner_id",
    )

    await documents.create_index(
        "status",
    )

    await documents.create_index(
        "created_at",
    )

    await documents.create_index(
        "filename",
    )

    await documents.create_index(
        "mime_type",
    )
    await documents.create_index(
        [
            ("owner_id", ASCENDING),
            ("file_hash", ASCENDING),
        ],
        unique=True,
        partialFilterExpression={
            "file_hash": {
                "$exists": True,
                "$type": "string",
            },
            "deleted_at": None,
        },
    )

async def create_document_content_indexes(db):
    document_contents = db[
        CollectionName.DOCUMENT_CONTENTS.value
    ]

    await document_contents.create_index(
        [("document_id", ASCENDING)]
    )

    await document_contents.create_index(
        [
            ("document_id", ASCENDING),
            ("page_number", ASCENDING),
        ],
        unique=True,
    )

async def create_document_chunk_indexes(db):

    chunks = db[
        CollectionName.DOCUMENT_CHUNKS.value
    ]

    await chunks.create_index(
        [
            ("document_id", ASCENDING),
        ]
    )

    await chunks.create_index(
        [
            ("document_id", ASCENDING),
            ("page_number", ASCENDING),
            ("chunk_index", ASCENDING),
        ],
        unique=True,
    )

async def create_processed_content_indexes(db):

    collection = db[
        CollectionName.PROCESSED_DOCUMENT_CONTENT.value
    ]

    await collection.create_index(
        [
            ("file_hash", ASCENDING),
        ],
        unique=True,
    )

async def create_document_image_indexes(db):

    document_images = db[
        CollectionName.DOCUMENT_IMAGES.value
    ]

    await document_images.create_index(
        [
            ("document_id", ASCENDING),
            ("page_number", ASCENDING),
            ("image_index", ASCENDING),
        ],
        unique=True,
    )

    await document_images.create_index(
        [("document_id", ASCENDING)]
    )

async def create_indexes(db):
    await create_user_indexes(db)
    await create_refresh_token_indexes(db)
    await create_request_log_indexes(db)
    await create_audit_log_indexes(db)
    await create_document_indexes(db)
    await create_document_content_indexes(db)
    await create_document_chunk_indexes(db)
    await create_processed_content_indexes(db)
    await create_document_image_indexes(db)
