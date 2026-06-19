from fastapi import HTTPException

VALID_TRANSITIONS = {
    "RECEIVED" : ["PREPARING", "CANCELLED"],
    "CANCELLED" : [],
    "PREPARING" : ["READY"],
    "READY": []
}

def validate_transitions(current: str, next_status: str):
    allowed = VALID_TRANSITIONS.get(current, [])
    if next_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current} to {next_status}"
        )