"""Initial reviewed core schema and private radar artifact metadata.

Revision ID: 0001_initial_postgis
Revises:
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = '0001_initial_postgis'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False))
    op.create_table('areas',
        sa.Column('area_id', sa.String(32), primary_key=True),
        sa.Column('resolution', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.String(32)),
        sa.Column('geom', Geometry('POLYGON', srid=4326, spatial_index=False)))
    op.create_index('idx_areas_geom', 'areas', ['geom'], postgresql_using='gist')
    op.create_table('datasets',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('product', sa.Text(), nullable=False),
        sa.Column('terms_url', sa.Text()),
        sa.Column('approved', sa.Boolean(), nullable=False))
    op.create_table('processing_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('parameter_hash', sa.String(64), nullable=False, unique=True))
    op.create_table('metric_values',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('area_id', sa.String(32), sa.ForeignKey('areas.area_id'), nullable=False),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('processing_runs.id'), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False),
        sa.Column('low', sa.Numeric()), sa.Column('high', sa.Numeric()),
        sa.Column('unit', sa.String(40), nullable=False),
        sa.Column('label', sa.String(20), nullable=False),
        sa.Column('source_id', sa.String(64), sa.ForeignKey('datasets.id'), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True)),
        sa.Column('safety_tag', sa.String(40), nullable=False),
        sa.CheckConstraint('low IS NULL OR high IS NULL OR low <= high'))
    op.create_index('ix_metric_values_area_id', 'metric_values', ['area_id'])
    op.create_index('ix_metric_values_metric', 'metric_values', ['metric'])
    op.create_table('shelter_candidates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('area_id', sa.String(32), sa.ForeignKey('areas.area_id'), nullable=False),
        sa.Column('geom', Geometry('POINT', srid=4326, spatial_index=False)),
        sa.Column('safety_tag', sa.String(40), nullable=False),
        sa.Column('release_at', sa.DateTime(timezone=True)))
    op.create_index('ix_shelter_candidates_area_id', 'shelter_candidates', ['area_id'])
    op.create_index('idx_shelter_candidates_geom', 'shelter_candidates', ['geom'],
                    postgresql_using='gist')
    op.create_table('radar_artifacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('area_id', sa.String(32), sa.ForeignKey('areas.area_id'), nullable=False),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('processing_runs.id'), nullable=False),
        sa.Column('source_id', sa.String(64), sa.ForeignKey('datasets.id'), nullable=False),
        sa.Column('schema_version', sa.String(20), nullable=False),
        sa.Column('artifact_version', sa.String(80), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('private_uri', sa.Text(), nullable=False),
        sa.Column('track', sa.Integer(), nullable=False),
        sa.Column('frame', sa.Integer(), nullable=False),
        sa.Column('polarizations', JSONB(), nullable=False),
        sa.Column('before_acquired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('after_acquired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_version', sa.String(100), nullable=False),
        sa.Column('qa_status', sa.String(40), nullable=False),
        sa.Column('safety_tag', sa.String(40), nullable=False),
        sa.CheckConstraint('track > 0 AND frame > 0'),
        sa.CheckConstraint('char_length(sha256) = 64'),
        sa.CheckConstraint('before_acquired_at < after_acquired_at'))
    op.create_index('ix_radar_artifacts_area_id_run_id', 'radar_artifacts', ['area_id', 'run_id'])
    op.create_table('radar_area_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('area_id', sa.String(32), sa.ForeignKey('areas.area_id'), nullable=False),
        sa.Column('artifact_id', sa.String(36), sa.ForeignKey('radar_artifacts.id'), nullable=False),
        sa.Column('classification', sa.String(30), nullable=False),
        sa.Column('anomaly_score', sa.Numeric()),
        sa.Column('evidence_label', sa.String(20), nullable=False),
        sa.Column('reason_codes', JSONB(), nullable=False),
        sa.Column('qa_status', sa.String(40), nullable=False),
        sa.Column('safety_tag', sa.String(40), nullable=False),
        sa.Column('release_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("classification IN ('Unknown', 'candidate_change', 'other_change')"),
        sa.CheckConstraint("classification <> 'Unknown' OR anomaly_score IS NULL"))
    op.create_index('ix_radar_area_results_area_id_artifact_id', 'radar_area_results',
                    ['area_id', 'artifact_id'])


def downgrade() -> None:
    op.drop_index('ix_radar_area_results_area_id_artifact_id', table_name='radar_area_results')
    op.drop_table('radar_area_results')
    op.drop_index('ix_radar_artifacts_area_id_run_id', table_name='radar_artifacts')
    op.drop_table('radar_artifacts')
    op.drop_index('idx_shelter_candidates_geom', table_name='shelter_candidates')
    op.drop_index('ix_shelter_candidates_area_id', table_name='shelter_candidates')
    op.drop_table('shelter_candidates')
    op.drop_index('ix_metric_values_metric', table_name='metric_values')
    op.drop_index('ix_metric_values_area_id', table_name='metric_values')
    op.drop_table('metric_values')
    op.drop_table('processing_runs')
    op.drop_table('datasets')
    op.drop_index('idx_areas_geom', table_name='areas')
    op.drop_table('areas')
    op.drop_table('users')
    # Keep PostGIS: this migration may not own the extension in an existing database.
