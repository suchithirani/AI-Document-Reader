from fastapi import APIRouter, Depends

from app.dependencies.service import get_database
from app.common.response import success_response
from app.modules.search.schema import (
    AskQuestionRequest,
)
from app.modules.search.service import (
    SearchService,
)

search_router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@search_router.post("/")
async def search_document(
    request: AskQuestionRequest,
    db=Depends(get_database),
):

    service = SearchService(db)

    result = await service.search(
        document_id=request.document_id,
        question=request.question,
    )

    return success_response(
        message="Search completed.",
        data=result,
    )