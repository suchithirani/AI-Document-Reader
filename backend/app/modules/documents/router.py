from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    UploadFile,
)
from typing import Annotated
from fastapi.responses import FileResponse

from app.common.response import paginated_response, success_response
from app.dependencies.auth import get_current_user
from app.dependencies.service import get_document_service
from app.modules.auth.model import User
from app.modules.documents.service import DocumentService
from app.dependencies.rate_limit import rate_limit
from app.modules.documents.schema import ProcessDocumentsRequest


document_router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@document_router.post("/upload",dependencies=[rate_limit(limit=5, window=60)],)
async def upload_document(
    request: Request,
    files: Annotated[
        list[UploadFile],
        File(
            description="Upload one or more documents",
        ),
    ],
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(
        get_document_service,
    ),
):
    
    result = await service.upload_document(
        request,
        current_user,
        files,
    )

    return success_response(
        message="Document uploaded successfully.",
        data=result,
        status_code=201,
    )

@document_router.get("",dependencies=[rate_limit(limit=10, window=60)],)
async def get_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(
        get_current_user,
    ),
    service: DocumentService = Depends(
        get_document_service,
    ),
):

    documents = await service.get_documents(
        current_user=current_user,
        skip=skip,
        limit=limit,
    )

    total = await service.count_documents(
        current_user,
    )

    return paginated_response(
        items=documents,
        total=total,
        page=(skip // limit) + 1,
        limit=limit,
    )

@document_router.get("/{document_id}",dependencies=[rate_limit(limit=10, window=60)],)
async def get_document(
    document_id: str,
    current_user: User = Depends(
        get_current_user,
    ),
    service: DocumentService = Depends(
        get_document_service,
    ),
):

    result = await service.get_document(
        current_user=current_user,
        document_id=document_id,
    )

    return success_response(
        message="Document fetched successfully.",
        data=result.model_dump(
            by_alias=True,
            mode="json",
        ),
    )

@document_router.get(
    "/{document_id}/download",
    response_class=FileResponse,
    dependencies=[rate_limit(limit=10, window=60)],
)
async def download_document(
    document_id: str,
    current_user: User = Depends(
        get_current_user,
    ),
    service: DocumentService = Depends(
        get_document_service,
    ),
):

    return await service.download_document(
        current_user=current_user,
        document_id=document_id,
    )

@document_router.delete("/{document_id}",dependencies=[rate_limit(limit=5, window=60)],)
async def delete_document(
    request: Request,
    document_id: str,
    current_user: User = Depends(
        get_current_user,
    ),
    service: DocumentService = Depends(
        get_document_service,
    ),
):

    result = await service.delete_document(
        http_request=request,
        current_user=current_user,
        document_id=document_id,
    )

    return success_response(
        message=result["message"],
    )

@document_router.post("/{document_id}/process",dependencies=[rate_limit(limit=3, window=60)],)
# async def process_document(
#     request: Request,
#     document_id: str,
#     current_user: User = Depends(
#         get_current_user,
#     ),
#     service: DocumentService = Depends(
#         get_document_service,
#     ),
# ):

#     result = await service.process_document(
#         http_request=request,
#         current_user=current_user,
#         document_id=document_id,
#     )

#     return success_response(
#         message="Document processed successfully.",
#         data=result,
#     )

@document_router.post(
    "/process",
    dependencies=[
        rate_limit(
            limit=3,
            window=60,
        )
    ],
)
async def process_documents(
    request: Request,
    body: ProcessDocumentsRequest,
    current_user: User = Depends(
        get_current_user,
    ),
    service: DocumentService = Depends(
        get_document_service,
    ),
):

    result = await service.process_documents(
        http_request=request,
        current_user=current_user,
        document_ids=body.document_ids,
    )

    return success_response(
        message="Documents queued for processing.",
        data=result,
    )