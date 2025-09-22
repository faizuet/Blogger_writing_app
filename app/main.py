from fastapi import FastAPI
from app.api import auth, blog

# Create FastAPI app
app = FastAPI(
    title="Blog App",
    description="A clean FastAPI blog application",
    version="1.0.0",
)

# Include routers
app.include_router(auth.router)
app.include_router(blog.router)

