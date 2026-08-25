from fastapi import APIRouter, Depends, status

from app.common.response import success_response
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import rate_limit
from app.dependencies.service import get_database
from app.modules.auth.model import User
from app.modules.document_collections.schema import (
    CreateDocumentCollectionRequest,
    DocumentCollectionResponse,
    UpdateDocumentCollectionRequest,
)
from app.modules.document_collections.service import DocumentCollectionService

document_collection_router = APIRouter(
    prefix="/document-collections",
    tags=["Document Collections"],
)

def get_collection_service(db=Depends(get_database)):
    return DocumentCollectionService(db)

@document_collection_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(limit=10, window=60)],
)
async def create_collection(
    body: CreateDocumentCollectionRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentCollectionService = Depends(get_collection_service),
):
    result = await service.create_collection(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        document_ids=body.document_ids,
    )

    response_data = DocumentCollectionResponse(
        id=str(result.id),
        owner_id=result.owner_id,
        name=result.name,
        description=result.description,
        document_ids=result.document_ids,
        document_count=len(result.document_ids),
        created_at=result.created_at.isoformat(),
        updated_at=result.updated_at.isoformat(),
    )

    return success_response(
        message="Collection created successfully.",
        data=response_data.model_dump(),
        status_code=201,
    )

@document_collection_router.get(
    "",
    dependencies=[rate_limit(limit=60, window=60)],
)
async def get_collections(
    current_user: User = Depends(get_current_user),
    service: DocumentCollectionService = Depends(get_collection_service),
):
    collections = await service.get_collections(current_user.id)

    results = [
        DocumentCollectionResponse(
            id=str(col.id),
            owner_id=col.owner_id,
            name=col.name,
            description=col.description,
            document_ids=col.document_ids,
            document_count=len(col.document_ids),
            created_at=col.created_at.isoformat(),
            updated_at=col.updated_at.isoformat(),
        ).model_dump()
        for col in collections
    ]

    return success_response(
        message="Collections retrieved successfully.",
        data=results,
    )

@document_collection_router.get(
    "/{collection_id}",
    dependencies=[rate_limit(limit=30, window=60)],
)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service: DocumentCollectionService = Depends(get_collection_service),
):
    col = await service.get_collection(current_user.id, collection_id)

    response_data = DocumentCollectionResponse(
        id=str(col.id),
        owner_id=col.owner_id,
        name=col.name,
        description=col.description,
        document_ids=col.document_ids,
        document_count=len(col.document_ids),
        created_at=col.created_at.isoformat(),
        updated_at=col.updated_at.isoformat(),
    )

    return success_response(
        message="Collection retrieved successfully.",
        data=response_data.model_dump(),
    )

@document_collection_router.put(
    "/{collection_id}",
    dependencies=[rate_limit(limit=30, window=60)],
)
async def update_collection(
    collection_id: str,
    body: UpdateDocumentCollectionRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentCollectionService = Depends(get_collection_service),
):
    col = await service.update_collection(
        owner_id=current_user.id,
        collection_id=collection_id,
        name=body.name,
        description=body.description,
        document_ids=body.document_ids,
    )

    response_data = DocumentCollectionResponse(
        id=str(col.id),
        owner_id=col.owner_id,
        name=col.name,
        description=col.description,
        document_ids=col.document_ids,
        document_count=len(col.document_ids),
        created_at=col.created_at.isoformat(),
        updated_at=col.updated_at.isoformat(),
    )

    return success_response(
        message="Collection updated successfully.",
        data=response_data.model_dump(),
    )

@document_collection_router.delete(
    "/{collection_id}",
    dependencies=[rate_limit(limit=30, window=60)],
)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    service: DocumentCollectionService = Depends(get_collection_service),
):
    await service.delete_collection(current_user.id, collection_id)

    return success_response(
        message="Collection deleted successfully.",
    )
