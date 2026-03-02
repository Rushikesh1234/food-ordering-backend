from fastapi import APIRouter, HTTPException, Depends
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantListResponse
from app.models.restaurant import Restaurant
from app.core.security import require_restaurant_owner_or_admin
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import Query
from typing import Optional

from app.services.restaurant_service.get_restaurant_service import get_restaurant, get_restaurants
from app.services.restaurant_service.create_restaurant_service import create_restaurant

router = APIRouter()

@router.get("/", response_model=RestaurantListResponse)
def get_restaurants_service(
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    name: Optional[str] = Query(None, description="Search query for restaurant name"),
    db: Session = Depends(get_db)
    ) -> RestaurantListResponse:
    return get_restaurants(db, last_id, size, name)

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_service(
    restaurant_id: int, 
    db: Session = Depends(get_db)
    ) -> RestaurantResponse:
    return get_restaurant(restaurant_id, db)

@router.post("/registerRestaurant", response_model=RestaurantResponse)
def create_restaurant_service( 
    restaurant: RestaurantCreate,
    db: Session = Depends(get_db), 
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ) -> RestaurantResponse:
    return create_restaurant(db, restaurant, restaurant_owner)