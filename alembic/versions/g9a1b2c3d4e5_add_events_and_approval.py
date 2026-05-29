"""add user approval

Revision ID: g9a1b2c3d4e5
Revises: f8850e3bdf8a
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g9a1b2c3d4e5'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_approved = true")
    op.alter_column('users', 'is_approved', nullable=False, server_default=sa.text('false'))


def downgrade() -> None:
    op.drop_column('users', 'is_approved')
