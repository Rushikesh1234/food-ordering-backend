from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from typing import Optional

from payment_service.logic.webhooks import stripe_webhook

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook_service(
        request: Request
    ):
    return stripe_webhook(request)