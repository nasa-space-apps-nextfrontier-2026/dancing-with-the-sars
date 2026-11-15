"""Suppressed real-mode public map response.

Real radar publication is intentionally hard-disabled. A future implementation
must bind approval to an immutable artifact and complete high-risk-cell, spatial
cohort, licence, and snapshot-differencing review before it may query PostGIS.
H3 r8 aggregation and a minimum count are not sufficient protection.
"""

from __future__ import annotations

from typing import Any


def _base() -> dict[str, Any]:
    return {
        "synthetic": False,
        "resolution": 8,
        "layers": [],
        "suppressed": True,
        "release_policy": "72h_and_review",
    }


def public_map() -> dict[str, Any]:
    """Return suppression without constructing an engine or querying PostGIS."""
    return _base()
