from fastapi import APIRouter, Query
from typing import Optional

from search_service.config.elasticsearch_config import es_client

from search_service.logic.search_query_service import search_query

from search_service.schemas.search import SearchResponse

router = APIRouter()

@router.get("/", response_model=SearchResponse)
async def search_service(
        q: str = Query(..., min_length=2, description="Search query for restaurant or menu item name"),
        category: Optional[str] = None,
        lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for location-based search"),
        lon: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for location-based search"),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100)
    ) -> SearchResponse:
    return await search_query(es_client, q, category, lat, lon, page, size)