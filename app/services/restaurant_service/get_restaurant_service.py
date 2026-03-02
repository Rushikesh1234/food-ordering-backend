from fastapi import APIRouter, HTTPException, Depends
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Query
from sqlalchemy import asc
from typing import Optional, cast

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantListResponse

def get_restaurant(restaurant_id: int, db: Session) -> RestaurantResponse:

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return RestaurantResponse.model_validate(restaurant)


def get_restaurants(
    db: Session,
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    name: Optional[str] = Query(None, description="Search query for restaurant name"),
    ) -> RestaurantListResponse:
    
    #if page < 1: 
    #    page = 1
    #offset = (page - 1) * size
    
    start_id = last_id if last_id >= 0 else 0

    query = db.query(Restaurant)

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))

    total_counts = int(query.count())

    # restaurants = query.filter(Restaurant.id > last_id).order_by(Restaurant.id).limit(size).all()

    restaurants = query.filter(Restaurant.id > start_id).order_by(asc(Restaurant.id)).limit(size).all()

    new_last_id = restaurants[-1].id if restaurants else last_id

    return RestaurantListResponse.model_validate({
        "total_counts": total_counts,
        "last_id": new_last_id,
        "size": size,
        "restaurants": restaurants
    })
