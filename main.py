from fastapi import FastAPI

from app.api import auth, restaurants, menu, orders

app = FastAPI(title="Food Ordering Backend", version="1.0.0")

app.include_router(auth.router, prefix='/auth', tags=['Auth'])
app.include_router(restaurants.router, prefix='/restaurants', tags=['Restaurants'])
app.include_router(menu.router, prefix='/menu', tags=['Menu'])
app.include_router(orders.router, prefix='/orders', tags=['Orders'])

@app.get("/health")
def health_check():
    return {"status": "ok"}
