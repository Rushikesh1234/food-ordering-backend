from typing import List
from decimal import Decimal
from pydantic import BaseModel

from payment_service.schemas.event_base import BaseEvent

class PaymentSucceededEvent(BaseEvent):
    event_type: str = "PaymentSucceeded"
    stripe_payment_intent_id: str
    order_id: int
    amount_paid: int