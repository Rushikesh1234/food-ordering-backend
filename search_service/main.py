from fastapi import FastAPI

from search_service.api import search

app = FastAPI(
    title="Search Microservice", 
    description= "Handles user search queries for restaurants and menu items",
    version="1.0.0",
)

app.include_router(search.router, prefix='/search', tags=['Search'])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "search_service"}
