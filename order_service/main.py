from fastapi import FastAPI

from order_service.api import orders

app = FastAPI(
    title="Order Management Microservice", 
    description="Handles order creation, status updates, and retrieval",
    version="1.0.0"
)

app.include_router(orders.router, prefix='/orders', tags=['Orders'])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "order_management_service"}