"""Authenticated map bundle for the Cesium frontend.

The bundle composes existing PostGIS-backed services.  It does not introduce a
second data store and it never fills absent scientific or humanitarian inputs
with demonstration values.  Missing domains are listed in ``unavailable`` so
the client can render an honest empty state.
"""

from __future__ import annotations

from typing import Any

import h3
from backend.app.core.security import Identity
from backend.app.services import agents_real, areas_real, live_real, radar_real, summary_real


def _centroids(cell_ids: set[str]) -> dict[str, list[float]]:
    centers: dict[str, list[float]] = {}
    for cell_id in cell_ids:
        try:
            lat, lon = h3.cell_to_latlng(cell_id)
        except (TypeError, ValueError, h3.H3BaseException):
            continue
        centers[cell_id] = [float(lat), float(lon)]
    return centers


def build(
    engine: Any,
    identity: Identity,
    area_id: str | None,
    limit: int,
) -> dict[str, Any]:
    """Return the current released, scoped data needed by the map screen."""
    unavailable: dict[str, str] = {
        "facilities": "Validated facility data is not loaded.",
        "shelters": "Validated shelter data is not loaded.",
        "routes": "Validated road and closure data is not loaded.",
    }

    try:
        incidents = agents_real.list_incidents(engine, identity, area_id, limit, 0)
    except agents_real.NotLoaded:
        incidents = {
            "synthetic": False,
            "generated_at": "",
            "weights": {},
            "data_age": {},
            "items": [],
            "next_cursor": None,
        }
        unavailable["incidents"] = "Reviewed agent outputs are not loaded."

    layers = {
        "synthetic": False,
        "items": radar_real.list_layers(identity),
        "next_cursor": None,
    }
    if not layers["items"]:
        unavailable["layers"] = "No released radar layer catalogue is loaded."

    alerts = live_real.list_alerts(
        engine,
        identity,
        area_id=area_id,
        kind=None,
        since=None,
        limit=100,
        offset=0,
    )

    details: dict[str, dict[str, Any]] = {}
    damage: dict[str, dict[str, Any]] = {}
    people: dict[str, dict[str, Any]] = {}
    budgets: dict[str, dict[str, Any]] = {}
    cell_ids: set[str] = set()

    for incident in incidents["items"]:
        incident_id = incident["incident_id"]
        incident_area = incident["area_id"]
        cell_ids.add(incident_area)

        detail = agents_real.get_incident(engine, identity, incident_id)
        if detail is not None:
            details[incident_id] = detail

        area_damage = radar_real.damage(engine, incident_area, None, identity)
        damage[incident_area] = area_damage
        if not area_damage["items"]:
            unavailable[f"damage:{incident_area}"] = (
                "No eligible released radar result is available; this is not a zero-impact result."
            )
        cell_ids.update(item["area_id"] for item in area_damage["items"])

        budget = agents_real.area_budget(engine, incident_area)
        if budget is not None:
            budgets[incident_area] = budget

        try:
            population = areas_real.people(engine, incident_area, identity)
        except summary_real.Unavailable:
            unavailable[f"people:{incident_area}"] = "Population evidence is not loaded."
        else:
            if population is not None:
                people[incident_area] = population

    cell_ids.update(alert["area_id"] for alert in alerts["items"])
    return {
        "synthetic": False,
        "generated_at": incidents["generated_at"],
        "incidents": incidents,
        "incident_details": details,
        "layers": layers,
        "damage": damage,
        "alerts": alerts,
        "people": people,
        "budgets": budgets,
        "centroids": _centroids(cell_ids),
        "unavailable": unavailable,
    }
