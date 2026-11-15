"""Alerts from the worker (fires, possible power loss) and per-source fetch status.

Alerts are stored at neighbourhood level (H3 r8 area id) only; exact detection coordinates are
never stored. source_status keeps the last successful fetch so the API can show Cached data when
a source fails.

Revision ID: 0003_alerts_and_source_status
Revises: 0002_metric_value_records
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = '0003_alerts_and_source_status'
down_revision = '0002_metric_value_records'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('alert_id', sa.String(64), primary_key=True),
        sa.Column('area_id', sa.String(32), nullable=False),
        sa.Column('type', sa.String(40), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('satellite', sa.String(80), nullable=False),
        sa.Column('product', sa.String(120), nullable=False),
        sa.Column('label', sa.String(20), nullable=False),
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('source', JSONB(), nullable=False),
        sa.Column('lineage_ids', JSONB(), nullable=False),
        sa.Column('independent_source_count', sa.Integer(), nullable=False),
        sa.Column('release_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('safety_tag', sa.String(40), nullable=False),
        sa.Column('review_status', sa.String(20), nullable=False, server_default='unreviewed'),
        sa.Column('detail', JSONB(), nullable=False),
        sa.CheckConstraint("label IN ('Observed', 'Reported', 'Corroborated', 'Unknown')"),
        sa.CheckConstraint("type IN ('fire_detected', 'possible_power_loss')"))
    op.create_index('ix_alerts_area_id', 'alerts', ['area_id'])
    op.create_index('ix_alerts_detected_at', 'alerts', ['detected_at'])
    op.create_table(
        'source_status',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('acquired_at', sa.DateTime(timezone=True)),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('last_success_at', sa.DateTime(timezone=True)),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('failure', sa.Text(), nullable=False, server_default=''),
        sa.Column('detail', JSONB(), nullable=False))


def downgrade() -> None:
    op.drop_table('source_status')
    op.drop_index('ix_alerts_detected_at', table_name='alerts')
    op.drop_index('ix_alerts_area_id', table_name='alerts')
    op.drop_table('alerts')
