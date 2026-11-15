"""72-hour release hold: a result is visible only once its release_at has passed."""

from __future__ import annotations

import datetime as dt


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def is_released(release_at: dt.datetime | str | None, now: dt.datetime | None = None) -> bool:
    """No release time means not releasable (never shown by default)."""
    if release_at is None:
        return False
    if isinstance(release_at, str):
        release_at = dt.datetime.fromisoformat(release_at)
    if release_at.tzinfo is None:
        raise ValueError("release_at must be timezone-aware")
    return release_at <= (now or now_utc())
