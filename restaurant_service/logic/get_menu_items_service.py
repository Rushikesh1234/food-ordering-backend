from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, cast

from restaurant_service.models.menu_item import MenuItem
from restaurant_service.models.restaurant import Restaurant

from restaurant_service.schemas.menu_item import MenuItemResponse

def get_menus(
        db: Session, 
        restaurant_id: int
    ) -> List[MenuItemResponse]:

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

def get_menu(
        db: Session, 
        menu_id: int
    ) -> MenuItemResponse:

    if menu_id is None:
        raise HTTPException(status_code=400, detail="MenuItem ID is required")
    
    menu = db.query(MenuItem).filter(MenuItem.id == menu_id).first()

    if not menu:
        raise HTTPException(status_code=404, detail="MenuItem not found")
    
    return MenuItemResponse.model_validate(menu)