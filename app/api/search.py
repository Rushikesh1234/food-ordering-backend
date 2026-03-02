from fastapi import APIRouter, Query
from typing import Optional

from app.db.elasticsearch_utils import es_client

from app.services.search_service.search_query_service import search_query

from app.schemas.search import SearchResponse

router = APIRouter()

@router.get("/", response_model=SearchResponse)
async def search_service(
    query: str = Query(..., min_length=2, description="Search query for restaurant or menu item name"),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
    ):
    return await search_query(es_client, query, category, page, size)