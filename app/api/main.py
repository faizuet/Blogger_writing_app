from fastapi import APIRouter
from app.api.routes import auth, blog

# Group all API routes
api_router = APIRouter()

#include routers
api_router.include_router(auth.router)
api_router.include_router(blog.router)

