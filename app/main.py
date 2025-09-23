from fastapi import FastAPI
from app.api.main import api_router

# Create FastAPI app
app = FastAPI(
    title="Blog App",
    description="A clean FastAPI blog application",
    version="1.0.0",
)

# Include all API routers
app.include_router(api_router)

