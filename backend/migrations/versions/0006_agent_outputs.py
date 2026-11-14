"""U-06: tables for the agents' output (ranking, recommendations, insights, budgets, buildings).

Loaded by scripts/load_agent_outputs.py from the worker's agent publish step. Restricted: read only
behind sign-in, role, area scope and release_at checks. No residents per building (doc 07).

Revision ID: 0006_agent_outputs
Revises: 0005_audit_reviews_access_jobs
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = '0006_agent_outputs'
down_revision = '0005_audit_reviews_access_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('run_id', sa.String(40), primary_key=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('loaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('counts', JSONB(), nullable=False))
    op.create_table(
        'agent_incidents',
        sa.Column('incident_id', sa.String(120), primary_key=True),
        sa.Column('area_id', sa.String(32), nullable=False),
        sa.Column('kind', sa.String(40), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score_low', sa.Float(), nullable=False),
        sa.Column('score_high', sa.Float(), nullable=False),
        sa.Column('release_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('record', JSONB(), nullable=False),
        sa.CheckConstraint("kind IN ('fire_detected', 'possible_power_loss', 'damage_candidate_area')",
                           name='ck_agent_incidents_kind'))
    op.create_index('ix_agent_incidents_area_id', 'agent_incidents', ['area_id'])
    op.create_table(
        'agent_recommendations',
        sa.Column('incident_id', sa.String(120),
                  sa.ForeignKey('agent_incidents.incident_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.String(20), primary_key=True),
        sa.Column('record', JSONB(), nullable=False),
        sa.CheckConstraint("role IN ('analyst', 'officer', 'coordinator')", name='ck_agent_recommendations_role'))
    op.create_table(
        'agent_insights',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('record', JSONB(), nullable=False))
    op.create_table(
        'agent_budgets',
        sa.Column('area_id', sa.String(32), primary_key=True),
        sa.Column('release_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('record', JSONB(), nullable=False))
    op.create_table(
        'agent_buildings',
        sa.Column('building_id', sa.String(40), primary_key=True),
        sa.Column('h3_r8', sa.String(32), nullable=False),
        sa.Column('release_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('geom', Geometry('GEOMETRY', srid=4326, spatial_index=False), nullable=True),
        sa.Column('properties', JSONB(), nullable=False))
    op.create_index('ix_agent_buildings_h3_r8', 'agent_buildings', ['h3_r8'])
    op.create_index('idx_agent_buildings_geom', 'agent_buildings', ['geom'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_agent_buildings_geom', table_name='agent_buildings')
    op.drop_index('ix_agent_buildings_h3_r8', table_name='agent_buildings')
    op.drop_table('agent_buildings')
    op.drop_table('agent_budgets')
    op.drop_table('agent_insights')
    op.drop_table('agent_recommendations')
    op.drop_index('ix_agent_incidents_area_id', table_name='agent_incidents')
    op.drop_table('agent_incidents')
    op.drop_table('agent_runs')
