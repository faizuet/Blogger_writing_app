import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# DB config
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("Missing DB_USER / DB_PASSWORD / DB_NAME in .env file")

# ----------------------------
# Async engine for FastAPI
# ----------------------------
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_async_db():
    """FastAPI dependency for async DB session"""
    async with AsyncSessionLocal() as session:
        yield session

# ----------------------------
# Sync engine for Alembic
# ----------------------------
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiomysql", "+pymysql")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True, future=True)

# ----------------------------
# Base and metadata
# ----------------------------
Base = declarative_base()

# Import models so Alembic can detect them
from app.models import User, Blog, Comment, Reaction  # noqa

metadata = Base.metadata

