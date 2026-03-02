from pydantic import BaseModel
from typing import List, Any

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
    results: List[SearchResult]