from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, cast

from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant

from app.schemas.menu_item import MenuItemResponse

def get_menus(db: Session, restaurant_id: int) -> List[MenuItemResponse]:

    if restaurant_id is None:
        raise HTTPException(status_code=400, detail="Restaurant ID is required")
    
    is_restaurant = db.query(Restaurant.id).filter(Restaurant.id == restaurant_id).first()
    if not is_restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menus = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()

    validated_menus: List[MenuItemResponse] = []
    for menu in menus:
        validated_menus.append(MenuItemResponse.model_validate(menu))

    return validated_menus