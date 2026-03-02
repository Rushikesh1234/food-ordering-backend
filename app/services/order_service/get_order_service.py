from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, Depends, Query
from typing import cast
from sqlalchemy import asc

from app.core.security import require_customer_or_admin

from app.schemas.order import OrderResponse

from app.models.order import Order
from app.models.user import User

from app.schemas.user import UserRole

def get_order(db: Session, current_user: User, order_id: int) -> OrderResponse:
    existing_orders = db.query(Order).options(joinedload(Order.order_items))

    existing_order = existing_orders.filter(Order.id == order_id)

    if cast(str, current_user.role) != UserRole.ADMIN:
        existing_order = existing_order.filter(Order.user_id == current_user.id)

    existing_order = existing_order.first()
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return existing_order

def get_orders(
    db: Session, 
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    
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
        "orders": existing_orders
    }
