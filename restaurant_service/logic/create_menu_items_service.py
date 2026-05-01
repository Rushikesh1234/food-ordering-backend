from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, cast
import uuid
from sqlalchemy.util import defaultdict

from restaurant_service.models.menu_item import MenuItem
from restaurant_service.models.restaurant import Restaurant
from restaurant_service.models.outbox import Outbox

from restaurant_service.schemas.user import UserAuthSchema, UserRole
from restaurant_service.schemas.menu_item import MenuItemCreate, MenuItemResponse
from restaurant_service.schemas.menu_item_events import MenuItemCreatedEvent

def create_menu_items(
        menu_item: List[MenuItemCreate], 
        db: Session,
        restaurant_owner: UserAuthSchema
    ) -> List[MenuItemResponse]:

    if not menu_item:
        raise HTTPException(status_code=400, detail="No menu items provided")

    items_by_restaurant = defaultdict(list)
    for item in menu_item:
        if item.restaurant_id is None:
            raise HTTPException(status_code=400, detail="All items must have a restaurant_id")
        items_by_restaurant[item.restaurant_id].append(item)

    # This solves the N+1 problem of fetching restaurant details for each menu item, 
    # we will fetch details of all unique restaurant ids in one query and create a map of restaurant id to restaurant details. 
    # This way we can avoid making multiple queries to fetch restaurant details for each menu item and we can also avoid making multiple queries to check if the user is owner of the restaurant or not.
    unique_restaurant_ids = set(items_by_restaurant.keys())
    restaurant_map = {
        r.id : r for r in db.query(Restaurant).filter(Restaurant.id.in_(unique_restaurant_ids)).all()
    }

    existing_menu_item_names_by_restaurnant = set(
        db.query(MenuItem.restaurant_id, MenuItem.name).filter(
            MenuItem.restaurant_id.in_(unique_restaurant_ids),
            MenuItem.name.in_([item.name for item in menu_item])
        ).all()
    )

    new_menu_items_to_add: List[tuple[MenuItem, str]] = []
    is_admin = cast(str, restaurant_owner.role) == UserRole.ADMIN

    try:
        for rid, items in items_by_restaurant.items():
            
            # Remove this check as I have added N+1 optimization to fetch all restaurant details in one query 
            # and create a map of restaurant id to restaurant details, 
            # so we can avoid making multiple queries to fetch restaurant details for each menu item 
            # and we can also avoid making multiple queries to check if the user is owner of the restaurant or not.
            '''
            restaurant = db.query(Restaurant).filter(Restaurant.id == rid).first()
            if not restaurant:
                raise HTTPException(status_code=404, detail=f"Restaurant ID {rid} not found")
            '''
            restaurant = restaurant_map.get(rid)
            if not restaurant:
                raise HTTPException(status_code=404, detail=f"Restaurant ID {rid} not found")

            is_restaurant_owner = cast(int, restaurant.owner_id) == restaurant_owner.id
            if not (is_admin or is_restaurant_owner):
                raise HTTPException(status_code=403, detail="Not authorized to add menu items to this restaurant")
            
            # Remove this check as I have added N+1 optimization to fetch 
            # all existing menu item names for all restaurants in one query and 
            # create a set of (restaurant_id, menu_item_name) for all existing menu items,
            '''
            incoming_menu_item_names = [item.name for item in items]
            existing_menu_item_names = { 
                row[0] for row in db.query(MenuItem.name).filter(
                    MenuItem.restaurant_id == rid,
                    MenuItem.name.in_(incoming_menu_item_names)
                ).all()
            }
            '''

            for item in items:
                if (rid, item.name) in existing_menu_item_names_by_restaurnant:
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
                data['price'] = item.price
                new_menu_item = MenuItem(**data)
                db.add(new_menu_item)

                new_menu_items_to_add.append((new_menu_item, cast(str,restaurant.name)))
        
        if not new_menu_items_to_add:
            raise HTTPException(status_code=400, detail="No new items were added or All provided menu items already exist for the restaurant")

        db.flush()

        for item, r_name in new_menu_items_to_add:
            event_data = MenuItemCreatedEvent(
                menuitem_id=cast(int,item.id),
                restaurant_id=cast(int,item.restaurant_id),
                restaurant_name=cast(str, r_name),
                menuitem_name=cast(str,item.name),
                menuitem_description=cast(str,item.description),
                menuitem_price=cast(int,item.price),
                menuitem_available=cast(bool, item.is_available)
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
        for menu_item, _ in new_menu_items_to_add:
            db.refresh(menu_item)
            validated_responses.append(MenuItemResponse.model_validate(menu_item))

        return validated_responses

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Could not create menu items") from e