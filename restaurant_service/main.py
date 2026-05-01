from fastapi import FastAPI

from restaurant_service.api import menus
from restaurant_service.api import restaurants

app = FastAPI(
    title="Restaurant & MenuItem Microservice", 
    description= "Handles restaurant registration and menu management",
    version="1.0.0",
)

app.include_router(restaurants.router, prefix='/restaurants', tags=['Restaurants'])
app.include_router(menus.router, prefix='/menu', tags=['Menu'])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "restaurant_menuitem_service"}
