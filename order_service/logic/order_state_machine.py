from fastapi import HTTPException

VALID_TRANSITIONS = {
    "CREATED": ["PENDING_PAYMENT", "CANCELLED"],
    "PENDING_PAYMENT": ["PAID", "PAYMENT_FAILED", "CANCELLED"],
    "PAID": ["ACCEPTED", "CANCELLED"],
    "ACCEPTED": ["PREPARING", "CANCELLED"],
    "PREPARING": ["READY"],
    "READY": ["ASSIGNED"],
    "ASSIGNED": ["PICKED_UP", "CANCELLED"],
    "PICKED_UP": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": []
}

def validate_transitions(current: str, next_status: str):
    allowed = VALID_TRANSITIONS.get(current, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current} to {next_status}"
        )