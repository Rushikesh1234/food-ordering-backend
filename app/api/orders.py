from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse

from app.core.security import require_customer_or_admin, require_order_updater

from app.models.user import User

from app.services.order_service.create_order_service import create_order
from app.services.order_service.update_order_status_service import update_order
from app.services.order_service.get_order_service import get_order, get_orders

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order_service(
    order: OrderCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    return create_order(db, current_user, order)

@router.put("/{order_id}/status/{new_status}", response_model=OrderResponse)
def update_order_service(
        order_id: int,
        new_status: str,
        driver_id: int | None = None,
        db: Session = Depends(get_db), 
        current_user: User = Depends(require_order_updater)
    ):
    return update_order(db, current_user, order_id, new_status, driver_id)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_service(
    order_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    return get_order(db, current_user, order_id)

@router.get("/", response_model=OrderListResponse)
def get_orders_service(
    last_id: int = Query(0, description="Last ID of the previous page"), 
    size: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_customer_or_admin)
    ):
    return get_orders(db, last_id, size, current_user)