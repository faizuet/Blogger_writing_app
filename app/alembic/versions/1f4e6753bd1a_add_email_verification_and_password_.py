"""add email verification and password reset fields

Revision ID: 1f4e6753bd1a
Revises: 4bcd70f1b09c
Create Date: 2025-10-08 07:46:29.295576+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f4e6753bd1a'
down_revision: Union[str, None] = '4bcd70f1b09c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix reaction column default consistency
    op.alter_column(
        'reactions',
        'deleted',
        existing_type=sa.BOOLEAN(),
        server_default=None,
        existing_nullable=False,
    )

    # --- Add new user fields safely ---
    op.add_column(
        'users',
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default='false',  # <-- important fix for existing users
        ),
    )
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))

    # --- Create indexes for faster lookups ---
    op.create_index(op.f('ix_users_verification_token'), 'users', ['verification_token'], unique=False)
    op.create_index(op.f('ix_users_reset_token'), 'users', ['reset_token'], unique=False)


def downgrade() -> None:
    # --- Remove added fields and indexes ---
    op.drop_index(op.f('ix_users_reset_token'), table_name='users')
    op.drop_index(op.f('ix_users_verification_token'), table_name='users')

    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')

    # Revert reaction default
    op.alter_column(
        'reactions',
        'deleted',
        existing_type=sa.BOOLEAN(),
        server_default=sa.text('false'),
        existing_nullable=False,
    )

