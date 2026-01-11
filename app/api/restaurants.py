from fastapi import APIRouter, HTTPException, Depends
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantListResponse
from app.models.restaurant import Restaurant
from app.core.security import require_restaurant_owner_or_admin
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import Query
from sqlalchemy import asc
from typing import Optional

router = APIRouter()

@router.get("/", response_model=RestaurantListResponse)
def list_restaurants(
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    name: Optional[str] = Query(None, description="Search query for restaurant name"),
    db: Session = Depends(get_db)
    ):
    
    #if page < 1: 
    #    page = 1
    #offset = (page - 1) * size
    
    if last_id < 0:
        last_id = 0

    query = db.query(Restaurant)

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))

    total_counts = query.count()

    # restaurants = query.filter(Restaurant.id > last_id).order_by(Restaurant.id).limit(size).all()

    restaurants = query.filter(Restaurant.id > last_id).order_by(asc(Restaurant.id))
    restaurants = restaurants.limit(size).all()

    new_last_id = restaurants[-1].id if restaurants else last_id

    return {
        "total_counts": total_counts,
        "last_id": new_last_id,
        "size": size,
        "restaurants": restaurants
    }

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: int, 
    db: Session = Depends(get_db)
    ):

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant

@router.post("/registerRestaurant", response_model=RestaurantResponse)
def register_restaurant(
    restaurant: RestaurantCreate, 
    db: Session = Depends(get_db), 
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ):

    existing_restaurant = db.query(Restaurant).filter(
        Restaurant.name == restaurant.name, 
        Restaurant.address == restaurant.address
    ).first()
    
    if existing_restaurant:
        raise HTTPException(status_code=400, detail="Restaurant with this name and address already exists")

    # simple way to add data in model
    '''
    new_restaurant = Restaurant(
        name=restaurant.name,
        address=restaurant.address,
        phone_number=restaurant.phone_number,
        owner_id=restaurant_owner.id
    )
    '''
    # best way to add data in model
    data = restaurant.model_dump(
        exclude_none=True,
        exclude={"id", "created_at", "updated_at"}
    )
    data['owner_id'] = restaurant_owner.id
    new_restaurant = Restaurant(**data)

    try:
        db.add(new_restaurant)
        db.commit()
        db.refresh(new_restaurant)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not register restaurant") from e

    return new_restaurant