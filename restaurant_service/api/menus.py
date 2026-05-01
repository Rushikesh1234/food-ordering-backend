from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, cast

from restaurant_service.security.security import require_restaurant_owner_or_admin

from restaurant_service.db.session import get_db

from restaurant_service.schemas.menu_item import MenuItemCreate, MenuItemResponse
from restaurant_service.schemas.user import UserAuthSchema

from restaurant_service.logic.get_menu_items_service import get_menus, get_menu
from restaurant_service.logic.create_menu_items_service import create_menu_items

router = APIRouter()

@router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItemResponse])
def get_menus_service(
        restaurant_id: int, db: 
        Session = Depends(get_db)
    ) -> List[MenuItemResponse]:
    return get_menus(db, restaurant_id)

@router.get("/restaurants/{menu_id}/menu", response_model=MenuItemResponse)
def get_menu_service(
        menu_id: int, db: 
        Session = Depends(get_db)
    ) -> MenuItemResponse:
    return get_menu(db, menu_id)

@router.post("/menu_items", response_model=List[MenuItemResponse])
def create_menu_item_service(
        menu_item: List[MenuItemCreate], 
        db: Session = Depends(get_db),
        restaurant_owner: UserAuthSchema = Depends(require_restaurant_owner_or_admin)
    ) -> List[MenuItemResponse]:
    return create_menu_items(menu_item, db, restaurant_owner)