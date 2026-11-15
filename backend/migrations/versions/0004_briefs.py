"""Stored area briefs (print / offline). Access is re-checked on every read.

Revision ID: 0004_briefs
Revises: 0003_alerts_and_source_status
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = '0004_briefs'
down_revision = '0003_alerts_and_source_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'briefs',
        sa.Column('report_id', sa.String(40), primary_key=True),
        sa.Column('owner', sa.String(100), nullable=False),
        sa.Column('owner_role', sa.String(20), nullable=False),
        sa.Column('area_id', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload', JSONB(), nullable=False))
    op.create_index('ix_briefs_area_id', 'briefs', ['area_id'])


def downgrade() -> None:
    op.drop_index('ix_briefs_area_id', table_name='briefs')
    op.drop_table('briefs')
