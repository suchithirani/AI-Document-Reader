from fastapi import APIRouter, Depends

from app.dependencies.service import get_database
from app.common.response import success_response
from app.modules.search.schema import (
    AskQuestionRequest,
)
from app.modules.search.service import (
    SearchService,
)
from app.dependencies.rate_limit import rate_limit

search_router = APIRouter(
    prefix="/search",
    tags=["Search"],
)
    

@search_router.post("/",dependencies=[rate_limit(limit=10, window=60)],)
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