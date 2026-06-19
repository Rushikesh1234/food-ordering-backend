from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import cast
from sqlalchemy import asc
from sqlalchemy.orm import Session
import uuid

from restaurant_service.schemas.kitchen_order import KitchenOrderResponse, KitchenOrdersResponse
from restaurant_service.schemas.kitchen_order_events import OrderAcceptedByRestaurant, OrderCancelledByRestaurant, OrderReadyByRestaurant

from restaurant_service.models.kitchen_order import KitchenOrder, KitchenOrderStatus
from restaurant_service.models.outbox import Outbox

from restaurant_service.logic.kitchen_order_state_machine import validate_transitions

def get_order(
        order_id: int,
        db: Session
    ) -> KitchenOrderResponse:
    order = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Kitchen order not found")
    return KitchenOrderResponse.model_validate(order)

def get_orders(
        restaurant_id: int,
        db: Session
    ) -> KitchenOrdersResponse:
    orders = db.query(KitchenOrder).filter(KitchenOrder.restaurant_id == restaurant_id).order_by(asc(KitchenOrder.created_at)).all()

    return KitchenOrdersResponse.model_validate({"orders": orders})

def accept_order(
        order_id: int,
        db:Session
    ) -> KitchenOrderResponse:
    order = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Kitchen order not found")
    
    old_status = str(order.status.value)

    validate_transitions(old_status, KitchenOrderStatus.PREPARING.value)

    order.status = KitchenOrderStatus.PREPARING

    event_data = OrderAcceptedByRestaurant(
        order_id = cast(int,order.order_id),
        restaurant_id = cast(int, order.restaurant_id),
        estimated_prep_time = 20
    )

    event_entry = Outbox(
        id = uuid.uuid4(),
        aggregatetype = "KitchenOrder",
        aggregateid = str(order.order_id),
        type = event_data.event_type,
        payload = event_data.model_dump(mode='json')
    )
    db.add(event_entry)

    db.commit()

    return KitchenOrderResponse.model_validate(order)
    
def cancel_order(
        order_id: int,
        db:Session
    ) -> KitchenOrderResponse:
    order = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Kitchen order not found")

    old_status = str(order.status.value)

    validate_transitions(old_status, KitchenOrderStatus.CANCELLED.value)

    order.status = KitchenOrderStatus.CANCELLED

    event_data = OrderCancelledByRestaurant(
        order_id = cast(int,order.order_id),
        restaurant_id = cast(int, order.restaurant_id)
    )

    event_entry = Outbox(
        id = uuid.uuid4(),
        aggregatetype = "KitchenOrder",
        aggregateid = str(order.order_id),
        type = event_data.event_type,
        payload = event_data.model_dump(mode='json')
    )
    db.add(event_entry)

    db.commit()

    return KitchenOrderResponse.model_validate(order)

def mark_order_ready(
        order_id: int,
        db:Session
    ) -> KitchenOrderResponse:
    order = db.query(KitchenOrder).filter(KitchenOrder.order_id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Kitchen order not found")
    
    old_status = str(order.status.value)

    validate_transitions(old_status, KitchenOrderStatus.READY.value)

    order.status = KitchenOrderStatus.READY

    event_data = OrderReadyByRestaurant(
        order_id = cast(int,order.order_id),
        restaurant_id = cast(int, order.restaurant_id)
    )

    event_entry = Outbox(
        id = uuid.uuid4(),
        aggregatetype = "KitchenOrder",
        aggregateid = str(order.order_id),
        type = event_data.event_type,
        payload = event_data.model_dump(mode='json')
    )
    db.add(event_entry)

    db.commit()

    return KitchenOrderResponse.model_validate(order)