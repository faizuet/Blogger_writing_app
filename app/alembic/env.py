import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

# ---------------- Project Path ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------- Import DB & Models ----------------
from app.core.database import Base, DATABASE_URL
import app.models  # noqa: Ensure models are imported for autogenerate

# ---------------- Alembic Config ----------------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ---------------- Sync engine for migrations ----------------
SYNC_DATABASE_URL = str(DATABASE_URL).replace("+aiomysql", "+pymysql")
engine = create_engine(SYNC_DATABASE_URL, echo=True, future=True)

# ---------------- Migration Runners ----------------
def run_migrations_offline():
    """Run migrations in 'offline' mode (no DB connection)."""
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode (sync connection)."""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# ---------------- Run ----------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

