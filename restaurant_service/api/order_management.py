from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import Query
from typing import List, Optional

from restaurant_service.db.session import get_db

from restaurant_service.schemas.kitchen_order import KitchenOrderResponse, KitchenOrdersResponse

from restaurant_service.logic.order_management_service import get_order, get_orders, accept_order, cancel_order, mark_order_ready

from restaurant_service.security.security import require_restaurant_owner_or_admin

router = APIRouter()

@router.get("/order/{order_id}", response_model=KitchenOrderResponse)
def get_order_service(
        order_id: int,
        db: Session = Depends(get_db)
    ):
    return get_order(order_id, db)

@router.get("/order/", response_model=KitchenOrdersResponse)
def get_orders_service(
        restaurant_id: int,
        db: Session = Depends(get_db)
    ):
    return get_orders(restaurant_id, db)

@router.post("/order/{order_id}/accept", response_model=KitchenOrderResponse)
def accept_order_service(
        order_id: int,
        db: Session = Depends(get_db),
        user=Depends(require_restaurant_owner_or_admin)
    ):
    return accept_order(order_id, db)

@router.post("/order/{order_id}/cancel", response_model=KitchenOrderResponse)
def cancel_order_service(
        order_id: int,
        db: Session = Depends(get_db),
        user=Depends(require_restaurant_owner_or_admin)
    ):
    return cancel_order(order_id, db)

@router.post("/order/{order_id}/ready", response_model=KitchenOrderResponse)
def mark_order_ready_service(
        order_id: int,
        db: Session = Depends(get_db),
        user=Depends(require_restaurant_owner_or_admin)
    ):
    return mark_order_ready(order_id, db)