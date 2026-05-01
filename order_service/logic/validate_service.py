from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from typing import cast

from order_service.schemas.order_item import OrderItemCreate

from order_service.models import LocalMenuItem, LocalRestaurant

def validate_restaurant(db: Session, restaurant_id: int) -> LocalRestaurant:
    restaurant = db.query(LocalRestaurant).filter(LocalRestaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

def validate_menu_items(db: Session, restaurant_id: int, order_items: list[OrderItemCreate]):
    validated_menu_items = []
    total_amount = 0

    for item in order_items:
        menu_item = db.query(LocalMenuItem).filter(LocalMenuItem.id == item.menu_item_id).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item with ID {item.menu_item_id} not found")
        if cast(int, menu_item.restaurant_id) != int(restaurant_id):
            raise HTTPException(status_code=400, detail=f"Menu item with ID {item.menu_item_id} does not belong to the specified restaurant")
        
        total_amount += (item.quantity * menu_item.price)

        validated_menu_items.append(
            {
                "menu_item": menu_item,
                "quantity": item.quantity,
                "price": menu_item.price
            }
        )
    
    return total_amount, validated_menu_items