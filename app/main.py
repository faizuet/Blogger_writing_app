from fastapi import FastAPI

from app.api.main import api_router

app = FastAPI(
    title="Blog App",
    description="A clean FastAPI blog application with v1 & v2 routes, including the friends feature.",
    version="1.0.0",
)

app.include_router(api_router)
