from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
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

class ShelterCandidate(Base):
    __tablename__ = 'shelter_candidates'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    area_id: Mapped[str] = mapped_column(ForeignKey('areas.area_id'), index=True)
    geom: Mapped[object | None] = mapped_column(Geometry('POINT', srid=4326, spatial_index=True), nullable=True)
    safety_tag: Mapped[str] = mapped_column(String(40), default='coordinator_shelter')
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
