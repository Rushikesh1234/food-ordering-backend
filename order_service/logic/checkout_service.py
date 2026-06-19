import stripe
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import cast

from order_service.config.payment_config import STRIPE_SECRET_KEY

from order_service.models.order import Order

stripe.api_key = STRIPE_SECRET_KEY

async def create_payment(
        order_id: int,
        db: Session
    ):

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount = cast(int, order.total_amount),
            currency = 'usd',
            metadata = cast(dict, {'order_id': cast(int, order.id)})
        )

        order.stripe_payment_intent_id = cast(str, intent.id) # type: ignore

        db.commit()

        return {"client_secret": intent.client_secret}

    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to create payment intent {e} for the order {order_id}")