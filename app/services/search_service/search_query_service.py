from typing import Optional
from fastapi import Query, HTTPException

from app.db.elasticsearch_utils import es_client

from app.schemas.search import SearchResult, SearchResponse

async def search_query(
    es_client,
    query: str = Query(..., min_length=2, description="Search query for restaurant or menu item name"),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
    ):
    from_idx = (page - 1) * size

    query_body = {
        "bool" : {
            "must": [
                {
                    "multi_match": {
                        "query": query,
                        "fields" : [
                            "restaurant_name^3",
                            "menuitem_name^3",
                            "menuitem_description^2"
                        ],
                        "fuzziness": "AUTO",
                        "prefix_length": 2
                    }
                }
            ]
        }
    }

    if category:
        query_body["bool"]["filter"] = [{
            "term": {
                "category.keyword": category
            }
        }]
    
    try:
        response = await es_client.search(
            index=["restaurants", "menuitems"],
            query=query_body,
            from_=from_idx,
            size=size
        )

        mapped_results = []
        for hit in response["hits"]["hits"]:
            index_name = hit["_index"]
            source = hit["_source"]

            if index_name == "restaurants":
                result = SearchResult(
                    type="restaurant",
                    id=str(source.get("restaurant_id")),
                    score=hit["_score"],
                    title=source.get("restaurant_name"),
                    subtitle=source.get("restaurant_address", "restaurant_phone_number"),
                    data=source
                )
            elif index_name == "menuitems":
                price = source.get("menuitem_price", 0)
                result = SearchResult(
                    type="menuitem",
                    id=str(source.get("menuitem_id")),
                    score=hit["_score"],
                    title=source.get("menuitem_name"),
                    subtitle=f"${price} - {source.get('restaurant_name', '')}",
                    data=source
                )
            mapped_results.append(result)
        
        return SearchResponse(
            total=response["hits"]["total"]["value"],
            page=from_idx // size + 1,
            size=size,
            results=mapped_results
        )
    
    except Exception as e:
        print(f"Error searching in Elasticsearch: {e}")
        raise HTTPException(status_code=500, detail="Search failed")