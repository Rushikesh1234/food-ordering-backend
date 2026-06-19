from fastapi import Request, HTTPException
import stripe

from payment_service.config.stripe_config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

from payment_service.logic.payment_processor import handle_payment_succeeded

stripe.api_key = STRIPE_SECRET_KEY

async def stripe_webhook(
        request: Request
    ):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook signature verification failed")
    
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        await handle_payment_succeeded(payment_intent)
    
    elif event["type"] == "payment_intent.payment_failed":
        pass

    return {"status": "success"}