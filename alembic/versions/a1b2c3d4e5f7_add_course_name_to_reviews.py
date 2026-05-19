"""add course_name to reviews

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-05-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f7'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reviews', sa.Column('course_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('reviews', 'course_name')
