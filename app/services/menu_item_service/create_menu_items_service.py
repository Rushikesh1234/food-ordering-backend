from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, cast
import uuid

from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.user import User
from app.models.outbox import Outbox

from app.schemas.menu_item import MenuItemCreate, MenuItemResponse
from app.schemas.user import UserRole
from app.schemas.menu_item_events import MenuItemCreatedEvent

from app.core.security import require_restaurant_owner_or_admin

def create_menu_items(
    menu_item: List[MenuItemCreate], 
    db: Session,
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ) -> List[MenuItemResponse]:

    if not menu_item:
        raise HTTPException(status_code=400, detail="No menu items provided")

    if menu_item and menu_item[0].restaurant_id is None:
        raise HTTPException(status_code=400, detail="Restaurant ID is required for menu items")

    target_restaurant_id = menu_item[0].restaurant_id
    restaurant = db.query(Restaurant).filter(Restaurant.id == target_restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    is_admin = cast(str, restaurant_owner.role) == UserRole.ADMIN
    is_restaurant_owner = cast(int, restaurant.owner_id) == restaurant_owner.id
    if not (is_admin or is_restaurant_owner):
        raise HTTPException(status_code=403, detail="Not authorized to add menu items to this restaurant")

    incoming_menu_item_names = [item.name for item in menu_item]

    existing_menu_item_rows = db.query(MenuItem.name).filter(
        MenuItem.restaurant_id == target_restaurant_id,
        MenuItem.name.in_(incoming_menu_item_names)
    ).all()

    existing_menu_item_names: set[str] = {str(row[0]) for row in existing_menu_item_rows}

    new_menu_items_to_add = []

    try:
        for item in menu_item:
            if item.name in existing_menu_item_names:
                continue
            
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

            db.add(new_menu_item)
            new_menu_items_to_add.append(new_menu_item)
        
        if not new_menu_items_to_add:
            raise HTTPException(status_code=400, detail="All provided menu items already exist for the restaurant")

        db.flush()

        for item in new_menu_items_to_add:
            event_data = MenuItemCreatedEvent(
                menuitem_id=cast(int,item.id),
                restaurant_id=cast(int,item.restaurant_id),
                restaurant_name=cast(str, restaurant.name),
                menuitem_name=cast(str,item.name),
                menuitem_description=cast(str,item.description),
                menuitem_price=cast(float,item.price)
            )

            event_entry = Outbox(
                id = uuid.uuid4(),
                aggregatetype = "MenuItem",
                aggregateid = str(item.id),
                type = event_data.event_type,
                payload = event_data.model_dump(mode='json')
            )
            db.add(event_entry)
        
        db.commit()

        validated_responses: List[MenuItemResponse] = []
        for menu_item in new_menu_items_to_add:
            db.refresh(menu_item)
            validated_responses.append(MenuItemResponse.model_validate(menu_item))

        return validated_responses

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Could not create menu items") from e