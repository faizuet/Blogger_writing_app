import os
import sys
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine

# ---------------- Project Path Setup ----------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# ---------------- Import App DB & Models ----------------
from app.core.database import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, Base
import app.models  # ensures all models are registered

# ---------------- Alembic Config ----------------
config = context.config

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ---------------- Database URL ----------------
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ---------------- Engine ----------------
engine = create_engine(SYNC_DATABASE_URL, echo=False, future=True)

# ---------------- Migration Functions ----------------
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,          # detect enum/type changes
            compare_server_default=True # detect default changes
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------- Entry Point ----------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

