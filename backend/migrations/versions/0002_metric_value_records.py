"""Keep the full contract record, its stable id and release time with each metric value.

The API must return MetricValue records exactly as docs/contracts/openapi.yaml defines them
(lineage, freshness, limitations, release_at, ...). 0001 stores only the core columns, so this
adds the contract value_id (unique), release_at (for the 72-hour hold) and the full record.

Revision ID: 0002_metric_value_records
Revises: 0001_initial_postgis
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = '0002_metric_value_records'
down_revision = '0001_initial_postgis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('metric_values', sa.Column('value_id', sa.String(160), nullable=True))
    op.add_column('metric_values', sa.Column('release_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('metric_values', sa.Column('record', JSONB(), nullable=True))
    op.create_unique_constraint('uq_metric_values_value_id', 'metric_values', ['value_id'])
    op.create_index('ix_metric_values_release_at', 'metric_values', ['release_at'])


def downgrade() -> None:
    op.drop_index('ix_metric_values_release_at', table_name='metric_values')
    op.drop_constraint('uq_metric_values_value_id', 'metric_values', type_='unique')
    op.drop_column('metric_values', 'record')
    op.drop_column('metric_values', 'release_at')
    op.drop_column('metric_values', 'value_id')
