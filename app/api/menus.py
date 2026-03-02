from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, cast

from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User

from app.schemas.menu_item import MenuItemCreate, MenuItemResponse
from app.schemas.user import UserRole

from app.core.security import require_restaurant_owner_or_admin

from app.db.session import get_db

from app.services.menu_item_service.get_menu_items_service import get_menus
from app.services.menu_item_service.create_menu_items_service import create_menu_items

router = APIRouter()

@router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItemResponse])
def get_menus_service(restaurant_id: int, db: Session = Depends(get_db)) -> List[MenuItemResponse]:
    return get_menus(db, restaurant_id)

@router.post("/menu_items", response_model=List[MenuItemResponse])
def create_menu_item_service(
    menu_item: List[MenuItemCreate], 
    db: Session = Depends(get_db),
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ) -> List[MenuItemResponse]:
    return create_menu_items(menu_item, db, restaurant_owner)