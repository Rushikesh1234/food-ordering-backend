from typing import cast
import uuid

from payment_service.models.outbox import Outbox

from payment_service.db.session import SessionLocal

from payment_service.schemas.payment_events import PaymentSucceededEvent

async def handle_payment_succeeded(payment_intent):
    internal_order_id = payment_intent.get('metadata', {}).get('order_id')
    amount_received = payment_intent.get('amount')

    with SessionLocal() as db:

        # need to add check in db if it alrady exist and check  db/redis quickly as well.
  
        event_data = PaymentSucceededEvent(
            stripe_payment_intent_id = cast(str, payment_intent['id']),
            order_id = cast(int, internal_order_id),
            amount_paid = cast(int, amount_received)
        )
        
        event_entry = Outbox(
            id = uuid.uuid4(),
            aggregatetype = "Payment",
            aggregateid = str(payment_intent['id']),
            type = event_data.event_type,
            payload = event_data.model_dump(mode='json')
        )
        
        db.add(event_entry)

        db.commit()
    
