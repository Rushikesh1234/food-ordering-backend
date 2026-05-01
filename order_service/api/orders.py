from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from order_service.db.session import get_db

from order_service.schemas.user import UserAuthSchema
from order_service.schemas.order import OrderCreate, OrderResponse, OrderListResponse

from order_service.security.security import require_customer_or_admin, require_order_updater

from order_service.logic.create_order_service import create_order
from order_service.logic.update_order_status_service import update_order
from order_service.logic.get_order_service import get_order, get_orders

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order_service(
        order: OrderCreate,
        db: Session = Depends(get_db), 
        current_user: UserAuthSchema = Depends(require_customer_or_admin)
    ):
    return create_order(order, db, current_user)

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_service(
        order_id: int,
        new_status: str,
        driver_id: Optional[int] = None,
        db: Session = Depends(get_db), 
        current_user: UserAuthSchema = Depends(require_order_updater)
    ):
    return update_order(db, current_user, order_id, new_status, driver_id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_service(
        order_id: int, 
        db: Session = Depends(get_db), 
        current_user: UserAuthSchema = Depends(require_customer_or_admin)
    ):
    return get_order(order_id, db, current_user)

@router.get("/", response_model=OrderListResponse)
def get_orders_service(
        last_id: int = Query(0, description="Last ID of the previous page"), 
        size: int = Query(20, ge=1, le=100), 
        db: Session = Depends(get_db), 
        current_user: UserAuthSchema = Depends(require_customer_or_admin)
    ):
    return get_orders(db, current_user, last_id, size)