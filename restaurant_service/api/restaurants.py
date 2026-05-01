from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import Query
from typing import Optional

from restaurant_service.db.session import get_db

from restaurant_service.security.security import require_restaurant_owner_or_admin

from restaurant_service.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantListResponse
from restaurant_service.schemas.user import UserAuthSchema

from restaurant_service.logic.get_restaurant_service import get_restaurant, get_restaurants
from restaurant_service.logic.create_restaurant_service import create_restaurant

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
        restaurant_owner: UserAuthSchema = Depends(require_restaurant_owner_or_admin)
    ) -> RestaurantResponse:
    return create_restaurant(db, restaurant, restaurant_owner)