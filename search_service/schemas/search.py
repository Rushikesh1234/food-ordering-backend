from pydantic import BaseModel
from typing import List, Any, Optional

class SearchResult(BaseModel):
    type: str
    id: str
    score: float
    title: str
    subtitle: str
    data: dict[str, Any]

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    top_match: Optional[SearchResult] = None
    restaurants: List[SearchResult]
    menu_items: List[SearchResult]