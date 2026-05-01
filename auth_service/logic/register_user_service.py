from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast
import uuid

from auth_service.db.session import get_db

from auth_service.schemas.user import UserCreate, UserResponse, UserRole
from auth_service.schemas.user_events import UserCreatedEvent

from auth_service.models.user import User
from auth_service.models.outbox import Outbox
from auth_service.models.driver_profiles import DriverProfile

from auth_service.logic.password_handler import hash_password

def register(
        user: UserCreate, 
        db: Session = Depends(get_db)
    ) -> UserResponse:
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:        
        new_user = User(
            email=user.email,
            hashed_password=hash_password(user.password),
            role=user.role
        )

        db.add(new_user)
        db.flush()

        driver_active_status = False
        if user.role == UserRole.DRIVER:
            if not user.driver_details:
                raise HTTPException(status_code=400, detail="Driver details required for driver role")

            profile = DriverProfile(
                user_id = new_user.id,
                license_number = user.driver_details.license_number,
                is_active = True,
                vehicle_details = user.driver_details.vehicle_details
            )
            db.add(profile)
            driver_active_status = True

        event_data = UserCreatedEvent(
            user_id= cast(int, new_user.id),
            role = cast(str, new_user.role.value),
            is_active= driver_active_status,
            name= cast(str,new_user.email)
        )

        event_entry = Outbox(
            id = uuid.uuid4(),
            aggregatetype = "User",
            aggregateid = str(new_user.id),
            type = event_data.event_type,
            payload = event_data.model_dump(mode='json')
        )
        db.add(event_entry)

        db.commit()
        db.refresh(new_user)
    
        return UserResponse.model_validate(new_user)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register user") from e
