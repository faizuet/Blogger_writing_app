from fastapi import APIRouter
from app.api.routes import auth, blogs_v1, blogs_v2

api_router = APIRouter()

api_router.include_router(auth.router)

api_router.include_router(blogs_v1.router)
api_router.include_router(blogs_v2.router)

