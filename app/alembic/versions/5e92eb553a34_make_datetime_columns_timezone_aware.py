"""Make datetime columns timezone-aware

Revision ID: 5e92eb553a34
Revises: 1f4e6753bd1a
Create Date: 2025-10-08 10:45:32.794283+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5e92eb553a34'
down_revision: Union[str, None] = '1f4e6753bd1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert naive timestamps to timezone-aware
    op.alter_column(
        'users',
        'verification_token_expires',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True
    )
    op.alter_column(
        'users',
        'reset_token_expires',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True
    )
    # Ensure boolean column has no server_default (optional)
    op.alter_column(
        'users',
        'is_verified',
        existing_type=sa.BOOLEAN(),
        server_default=None,
        existing_nullable=False
    )


def downgrade() -> None:
    # Revert timezone-aware columns back to naive timestamps
    op.alter_column(
        'users',
        'reset_token_expires',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True
    )
    op.alter_column(
        'users',
        'verification_token_expires',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True
    )
    # Restore server default for boolean column
    op.alter_column(
        'users',
        'is_verified',
        existing_type=sa.BOOLEAN(),
        server_default=sa.text('false'),
        existing_nullable=False
    )

