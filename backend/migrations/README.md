# Database foundation

`python -m backend.app.db.migrations` is not a migration CLI. Run `python scripts/initialize_database.py` once against the local PostGIS service. The scaffold defines an initial SQLAlchemy schema; Alembic is installed for the first reviewed migration in M3-01. Schema expansion and production migration history remain unfinished.
