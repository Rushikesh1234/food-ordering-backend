from fastapi import FastAPI

from app.api import auth, menus, restaurants, orders, drivers, search

from app.db.elasticsearch_utils import es_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if await es_client.ping():
            print("Successfully connected to Elasticsearch")
    except Exception as e:
        print(f"Elasticsearch connection failed: {e}")

    yield

    await es_client.close()
    print("Elasticsearch connection closed")

app = FastAPI(
    title="Food Ordering Backend", 
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router, prefix='/auth', tags=['Auth'])
app.include_router(restaurants.router, prefix='/restaurants', tags=['Restaurants'])
app.include_router(menus.router, prefix='/menu', tags=['Menu'])
app.include_router(orders.router, prefix='/orders', tags=['Orders'])
app.include_router(search.router, prefix='/search', tags=['Search'])

@app.get("/health")
def health_check():
    return {"status": "ok"}