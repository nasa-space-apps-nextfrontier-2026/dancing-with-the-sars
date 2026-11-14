"""Audit events, alert reviews, role changes and manual job runs.

Audit rows hold only actor, action, coarse resource type, outcome, time and request id: no
coordinates, tokens or request bodies (doc 05). Kept 30 days (pruned by the worker).

Revision ID: 0005_audit_reviews_access_jobs
Revises: 0004_briefs
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = '0005_audit_reviews_access_jobs'
down_revision = '0004_briefs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_events',
        sa.Column('id', sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column('actor_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(40), nullable=False),
        sa.Column('resource_type', sa.String(40), nullable=False),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_id', sa.String(64), nullable=True))
    op.create_index('ix_audit_events_at', 'audit_events', ['at'])
    op.create_table(
        'alert_reviews',
        sa.Column('review_id', sa.String(32), primary_key=True),
        sa.Column('alert_id', sa.String(64), sa.ForeignKey('alerts.alert_id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('actor_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('reviewed', 'needs_follow_up', 'not_relevant')",
                           name='ck_alert_reviews_status'))
    op.create_index('ix_alert_reviews_alert_id', 'alert_reviews', ['alert_id'])
    op.create_table(
        'user_access',
        sa.Column('user_id', sa.String(100), primary_key=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('area_scopes', JSONB(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('changed_by', sa.String(100), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('analyst', 'officer', 'coordinator', 'admin')", name='ck_user_access_role'))
    op.create_table(
        'job_runs',
        sa.Column('idempotency_key', sa.String(100), primary_key=True),
        sa.Column('job_id', sa.String(40), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('actor_id', sa.String(100), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_table('job_runs')
    op.drop_table('user_access')
    op.drop_index('ix_alert_reviews_alert_id', table_name='alert_reviews')
    op.drop_table('alert_reviews')
    op.drop_index('ix_audit_events_at', table_name='audit_events')
    op.drop_table('audit_events')
