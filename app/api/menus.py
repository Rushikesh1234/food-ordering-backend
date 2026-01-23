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

router = APIRouter()

@router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItemResponse])
def get_menu(
    restaurant_id: int, 
    db: Session = Depends(get_db)
    ):
    menus = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()

    if not menus:
        raise HTTPException(status_code=404, detail="Menu not found for the restaurant")

    return menus

@router.post("/menu_items", response_model=List[MenuItemResponse])
def create_menu_item(
    menu_item: List[MenuItemCreate], 
    db: Session = Depends(get_db),
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ):

    new_menu_items_to_add = []

    for item in menu_item:
        restaurant = db.query(Restaurant).filter(Restaurant.id == item.restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")

        if cast(str, restaurant_owner.role) != UserRole.ADMIN and cast(int, restaurant.owner_id) != restaurant_owner.id:
            raise HTTPException(status_code=403, detail="Not authorized to add menu items to this restaurant")

        existing_menu_item = db.query(MenuItem).filter(
            MenuItem.restaurant_id == item.restaurant_id,
            MenuItem.name == item.name
        ).first()
        if existing_menu_item:
            raise HTTPException(status_code=400, detail="Menu item with this name already exists for the restaurant")

        # simple way to add add in model
        '''
        new_menu_item = MenuItem(
            restaurant_id=item.restaurant_id,
            name=item.name,
            description=item.description,
            price=item.price
        )
        '''

        # best way to add data in model
        data = item.model_dump(
            exclude_none=True,
            exclude={"id", "created_at", "updated_at"}
        )
        data['restaurant_id'] = restaurant.id
        new_menu_item = MenuItem(**data)

        new_menu_items_to_add.append(new_menu_item)

    if new_menu_items_to_add:
        try:
            db.add_all(new_menu_items_to_add)
            db.commit()
            for menu_item in new_menu_items_to_add:
                db.refresh(menu_item)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Could not create menu items") from e

    return new_menu_items_to_add