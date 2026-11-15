"""Facilities (K-03, OpenStreetMap): clinics, hospitals, schools, water and power sites inside Lebanon.

Loaded by scripts/load_facilities.py. Restricted (doc 07): read only behind sign-in, role and area
scope; analysts get type and status without the exact location, officer and above get the point.
Names are not stored.

Revision ID: 0007_facilities
Revises: 0006_agent_outputs
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = '0007_facilities'
down_revision = '0006_agent_outputs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'facility_runs',
        sa.Column('run_id', sa.String(40), primary_key=True),
        sa.Column('loaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('counts', JSONB(), nullable=False))
    op.create_table(
        'facilities',
        sa.Column('facility_id', sa.String(80), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('h3_r9', sa.String(32), nullable=False),
        sa.Column('h3_r8', sa.String(32), nullable=False),
        sa.Column('osm_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('geom', Geometry('POINT', srid=4326, spatial_index=False), nullable=False),
        sa.CheckConstraint("type IN ('clinic', 'hospital', 'school', 'water', 'power')",
                           name='ck_facilities_type'))
    op.create_index('ix_facilities_h3_r8', 'facilities', ['h3_r8'])
    op.create_index('ix_facilities_h3_r9', 'facilities', ['h3_r9'])
    op.create_index('ix_facilities_geom', 'facilities', ['geom'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('ix_facilities_geom', table_name='facilities')
    op.drop_index('ix_facilities_h3_r9', table_name='facilities')
    op.drop_index('ix_facilities_h3_r8', table_name='facilities')
    op.drop_table('facilities')
    op.drop_table('facility_runs')
