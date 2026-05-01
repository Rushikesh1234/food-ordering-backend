from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_service.api import auth

app = FastAPI(
    title="Auth Microservice", 
    description= "Handles User Identity, Roles, and JWT Generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix='/auth', tags=['Authentication'])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth_service", "database": "connected"}