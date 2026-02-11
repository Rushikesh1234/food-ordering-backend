from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as session, joinedload
from sqlalchemy import asc
from typing import cast

from app.db.session import get_db

from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse
from app.schemas.user import UserRole

from app.core.security import require_customer_or_admin, require_order_updater

from app.models.user import User
from app.models.order import Order

from app.services.order_validation_service import order_service as order_service
from app.services.order_validation_service import order_status_service as order_status_service

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate, 
    db: session = Depends(get_db), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    return order_service.create_order(db, current_user, order)

@router.put("/{order_id}/status/{new_status}", response_model=OrderResponse)
def change_order_status(
        order_id: int,
        new_status: str,
        driver_id: int | None = None,
        db: session = Depends(get_db), 
        current_user: User = Depends(require_order_updater)
    ):
    return order_status_service.update_order_status(db, current_user, order_id, new_status, driver_id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int, 
    db: session = Depends(get_db), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    
    existing_order = db.query(Order).options(joinedload(Order.order_items))

    existing_order = existing_order.filter(Order.id == order_id)

    if cast(str, current_user.role) != UserRole.ADMIN:
        existing_order = existing_order.filter(Order.user_id == current_user.id)

    existing_order = existing_order.first()
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return existing_order

@router.get("/", response_model=OrderListResponse)
def list_orders(
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    db: session = Depends(get_db), 
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

    existing_orders = existing_orders.filter(Order.id > last_id).order_by(asc(Order.id))
    existing_orders = existing_orders.limit(size).all()

    new_last_id = existing_orders[-1].id if existing_orders else last_id

    return {
        "total_counts": total_counts,
        "last_id": new_last_id,
        "size": size,
        "orders": existing_orders
    }
