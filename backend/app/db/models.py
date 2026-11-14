from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def uid() -> str:
    return str(uuid4())

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class Area(Base):
    __tablename__ = 'areas'
    area_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    resolution: Mapped[int] = mapped_column(Integer)
    parent_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    geom: Mapped[object | None] = mapped_column(Geometry('POLYGON', srid=4326, spatial_index=True), nullable=True)

class Dataset(Base):
    __tablename__ = 'datasets'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(Text)
    product: Mapped[str] = mapped_column(Text)
    terms_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

class ProcessingRun(Base):
    __tablename__ = 'processing_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    status: Mapped[str] = mapped_column(String(20))
    parameter_hash: Mapped[str] = mapped_column(String(64), unique=True)

class MetricValue(Base):
    __tablename__ = 'metric_values'
    __table_args__ = (CheckConstraint('low IS NULL OR high IS NULL OR low <= high'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    area_id: Mapped[str] = mapped_column(ForeignKey('areas.area_id'), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey('processing_runs.id'))
    metric: Mapped[str] = mapped_column(String(100), index=True)
    low: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    high: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    unit: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safety_tag: Mapped[str] = mapped_column(String(40))
    # 0002: stable contract id, 72-hour release time and the full contract record.
    value_id: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,
                                                        index=True)
    record: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

class ShelterCandidate(Base):
    __tablename__ = 'shelter_candidates'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    area_id: Mapped[str] = mapped_column(ForeignKey('areas.area_id'), index=True)
    geom: Mapped[object | None] = mapped_column(Geometry('POINT', srid=4326, spatial_index=True), nullable=True)
    safety_tag: Mapped[str] = mapped_column(String(40), default='coordinator_shelter')
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RadarArtifact(Base):
    __tablename__ = 'radar_artifacts'
    __table_args__ = (
        CheckConstraint('track > 0 AND frame > 0'),
        CheckConstraint('char_length(sha256) = 64'),
        CheckConstraint('before_acquired_at < after_acquired_at'),
        Index('ix_radar_artifacts_area_id_run_id', 'area_id', 'run_id'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    area_id: Mapped[str] = mapped_column(ForeignKey('areas.area_id'))
    run_id: Mapped[str] = mapped_column(ForeignKey('processing_runs.id'))
    source_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'))
    schema_version: Mapped[str] = mapped_column(String(20))
    artifact_version: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    private_uri: Mapped[str] = mapped_column(Text)
    track: Mapped[int] = mapped_column(Integer)
    frame: Mapped[int] = mapped_column(Integer)
    polarizations: Mapped[list] = mapped_column(JSONB)
    before_acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    after_acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processing_version: Mapped[str] = mapped_column(String(100))
    qa_status: Mapped[str] = mapped_column(String(40))
    safety_tag: Mapped[str] = mapped_column(String(40))


class RadarAreaResult(Base):
    __tablename__ = 'radar_area_results'
    __table_args__ = (
        CheckConstraint("classification IN ('Unknown', 'candidate_change', 'other_change')"),
        CheckConstraint("classification <> 'Unknown' OR anomaly_score IS NULL"),
        Index('ix_radar_area_results_area_id_artifact_id', 'area_id', 'artifact_id'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    area_id: Mapped[str] = mapped_column(ForeignKey('areas.area_id'))
    artifact_id: Mapped[str] = mapped_column(ForeignKey('radar_artifacts.id'))
    classification: Mapped[str] = mapped_column(String(30))
    anomaly_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    evidence_label: Mapped[str] = mapped_column(String(20))
    reason_codes: Mapped[list] = mapped_column(JSONB)
    qa_status: Mapped[str] = mapped_column(String(40))
    safety_tag: Mapped[str] = mapped_column(String(40))
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
