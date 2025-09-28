"""Rename owner_id to user_id in blogs

Revision ID: fa629b30cbb3
Revises: 6abdd453c731
Create Date: 2025-09-28 15:25:38.897389
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fa629b30cbb3"
down_revision: Union[str, None] = "6abdd453c731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column owner_id -> user_id
    op.alter_column(
        "blogs",
        "owner_id",
        new_column_name="user_id",
        existing_type=sa.String(36),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Rollback: rename column user_id -> owner_id
    op.alter_column(
        "blogs",
        "user_id",
        new_column_name="owner_id",
        existing_type=sa.String(36),
        existing_nullable=False,
    )

