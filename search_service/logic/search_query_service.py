from typing import Optional
from fastapi import Query, HTTPException
import json

from search_service.schemas.search import SearchResult, SearchResponse

async def search_query(
        es_client,
        q: str = Query(..., min_length=2, description="Search query for restaurant or menu item name"),
        category: Optional[str] = None,
        lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for location-based search"),
        lon: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for location-based search"),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100)
    ) -> SearchResponse:
    from_idx = (page - 1) * size

    query_body = {
        "bool" : {
            "must": [
                {
                    "multi_match": {
                        "query": q,
                        "fields" : [
                            "restaurant_name^3",
                            "menuitem_name^3",
                            "menuitem_description^2"
                        ],
                        "fuzziness": "AUTO",
                        "prefix_length": 2
                    }
                }
            ],
            "should": [
                {
                    "term": {
                        "_index": {
                            "value": "restaurants",
                            "boost": 2.0
                        }
                    }
                }
            ],
            "filter": []
        }
    }

    if category:
        query_body["bool"]["filter"].append({
            "bool": {
            "should": [
                { "match": { "category": category } },
                { "bool": { "must_not": { "exists": { "field": "category" } } } } # Keep items
            ]
        }
        })
    
    query = query_body
    
    if lat is not None and lon is not None:
        query = {
            "function_score": {
                "query": query_body,
                "functions":[
                    {
                        "gauss": {
                            "location": {
                                "origin": {"lat": lat, "lon": lon},
                                "offset": "5km",
                                "scale": "10km"
                            }
                        }
                    }
                ],
                "boost_mode": "multiply"
            }
        }
    else:
        query = query_body

    try:
        print(f"DEBUG: Index: ['restaurants', 'menuitems'], Body: {json.dumps(query_body, indent=2)}")
        
        response = await es_client.search(
            index="*",
            query=query,
            from_=from_idx,
            size=size
        )

        restaurants = []
        menu_items = []

        for hit in response["hits"]["hits"]:
            index_name = hit["_index"]
            source = hit["_source"]
            score = hit["_score"]

            if index_name == "restaurants":
                result = SearchResult(
                    type="restaurant",
                    id=str(source.get("restaurant_id")),
                    score=score,
                    title=source.get("restaurant_name"),
                    subtitle=source.get("restaurant_address", "restaurant_phone_number"),
                    data=source
                )
                restaurants.append(result)
            elif index_name == "menuitems":
                price = source.get("menuitem_price", 0)
                result = SearchResult(
                    type="menuitem",
                    id=str(source.get("menuitem_id")),
                    score=score,
                    title=source.get("menuitem_name"),
                    subtitle=f"${price} - {source.get('restaurant_name', '')}",
                    data=source
                )
                menu_items.append(result)
        
        top_match = None

        all_candidates = restaurants + menu_items
        if all_candidates:
            top_match = all_candidates[0]

        response = {
            "total":response["hits"]["total"]["value"],
            "page":from_idx // size + 1,
            "size":size,
            "top_match":top_match,
            "restaurants":restaurants,
            "menu_items": menu_items
        }
        return SearchResponse.model_validate(response)
    
    except Exception as e:
        print(f"Error searching in Elasticsearch: {e}")
        raise HTTPException(status_code=500, detail="Search failed")