"""add cover_url to users

Revision ID: ab55856a2230
Revises: 
Create Date: 2025-11-21 ...

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'ab55856a2230'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('cover_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'cover_url')