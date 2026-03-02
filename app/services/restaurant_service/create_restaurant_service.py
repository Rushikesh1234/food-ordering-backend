from fastapi import HTTPException, Depends
from typing import cast
import uuid

from app.core.security import require_restaurant_owner_or_admin

from sqlalchemy.orm import Session

from app.schemas.restaurant import RestaurantCreate, RestaurantResponse

from app.models.restaurant import Restaurant
from app.models.user import User
from app.models.outbox import Outbox

from app.schemas.restaurant_events import RestaurantCreatedEvent

def create_restaurant(
    db: Session,
    restaurant: RestaurantCreate,
    restaurant_owner: User = Depends(require_restaurant_owner_or_admin)
    ) -> RestaurantResponse:
    try:
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

        db.add(new_restaurant)
        db.flush()

        event_data = RestaurantCreatedEvent(
            restaurant_id = cast(int, new_restaurant.id),
            restaurant_name = cast(str, new_restaurant.name),
            restaurant_address = cast(str, new_restaurant.address),
            restaurant_phone_number = cast(str, new_restaurant.phone_number),
            owner_id = cast(int, new_restaurant.owner_id) 
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
        raise HTTPException(status_code=500, detail="Could not register restaurant") from e