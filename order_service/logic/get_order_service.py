from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, Depends, Query
from typing import cast, Any, Dict
from sqlalchemy import asc

from order_service.schemas.order import OrderResponse
from order_service.schemas.user import UserAuthSchema, UserRole

from order_service.models.order import Order

def get_order(
        order_id: int,
        db: Session, 
        current_user: UserAuthSchema
    ) -> OrderResponse:

    existing_orders = db.query(Order).options(joinedload(Order.order_items))

    existing_order = existing_orders.filter(Order.id == order_id)

    if cast(str, current_user.role) != UserRole.ADMIN:
        existing_order = existing_order.filter(Order.user_id == current_user.id)

    existing_order = existing_order.first()
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse.model_validate(existing_order)

def get_orders(
        db: Session, 
        current_user: UserAuthSchema,
        last_id: int = Query(0, description="Last ID of the previous page"), 
        size: int = Query(20, ge=1, le=100)
    ) -> Dict[str, Any]:
    
    # For Offset pagination - page based
    #if page < 1:
    #    page = 1
    #offset = (page - 1) * size
   
    # For Keyset pagination - last_id based
    if last_id < 0:
        last_id = 0

    existing_orders = db.query(Order).options(joinedload(Order.order_items))

    if cast(str,current_user.role) != UserRole.ADMIN:
        existing_orders = existing_orders.filter(Order.user_id == current_user.id)

    # total_counts = existing_orders.count()
    # orders = existing_orders.offset(offset).limit(size).all()

    total_counts = existing_orders.count()

    existing_orders = existing_orders.filter(Order.id > last_id).order_by(asc(Order.id)).limit(size).all()
    new_last_id = existing_orders[-1].id if existing_orders else last_id

    return {
        "total_counts": total_counts,
        "last_id": new_last_id,
        "size": size,
        "orders": [OrderResponse.model_validate(o) for o in existing_orders]
    }
