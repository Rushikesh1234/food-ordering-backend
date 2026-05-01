from fastapi import HTTPException, Depends
from typing import cast
from sqlalchemy.orm import Session
import uuid

from restaurant_service.schemas.user import UserAuthSchema

from restaurant_service.models.outbox import Outbox
from restaurant_service.models.restaurant import Restaurant

from restaurant_service.schemas.restaurant import RestaurantCreate, RestaurantResponse
from restaurant_service.schemas.restaurant import AddressSchema, ContactSchema
from restaurant_service.schemas.restaurant_events import RestaurantCreatedEvent

def create_restaurant(
        db: Session,
        restaurant: RestaurantCreate,
        restaurant_owner: UserAuthSchema
    ) -> RestaurantResponse:
    
    try:
        existing_restaurant = db.query(Restaurant).filter(
            Restaurant.name == restaurant.name, 
            Restaurant.slug == restaurant.slug,
            Restaurant.address == restaurant.address.model_dump(exclude_none=True)
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
            mode='json',
            exclude_none=True,
            exclude={"id", "created_at", "updated_at"}
        )
        data['owner_id'] = restaurant_owner.id
        new_restaurant = Restaurant(**data)

        db.add(new_restaurant)
        db.flush()

        event_data = RestaurantCreatedEvent(
            restaurant_id = cast(int, new_restaurant.id),
            restaurant_name = cast(str, new_restaurant.name),
            restaurant_slug = cast(str, new_restaurant.slug),
            contact = ContactSchema(**restaurant.contact.model_dump()),
            address = AddressSchema(**restaurant.address.model_dump()),
            owner_id = cast(int, new_restaurant.owner_id),
            is_active=restaurant.settings.is_accepting_orders if not isinstance(restaurant.settings, dict) else restaurant.settings.get('is_accepting_orders', True)
        )

        event_entry = Outbox(
            id = uuid.uuid4(),
            aggregatetype = "Restaurant",
            aggregateid = str(new_restaurant.id),
            type = event_data.event_type,
            payload = event_data.model_dump(mode='json')
        )
        db.add(event_entry)
        
        db.commit()
        db.refresh(new_restaurant)

        return RestaurantResponse.model_validate(new_restaurant)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail= f"Could not register restaurant {str(e)}") from e