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
from backend.app.services import (
    agents_real,
    areas_real,
    facilities_real,
    live_real,
    radar_real,
    summary_real,
)


def _centroids(cell_ids: set[str]) -> dict[str, list[float]]:
    centers: dict[str, list[float]] = {}
    for cell_id in cell_ids:
        try:
            lat, lon = h3.cell_to_latlng(cell_id)
        except (TypeError, ValueError, h3.H3BaseException):
            continue
        centers[cell_id] = [float(lat), float(lon)]
    return centers


NIGHT_LIGHT_SOURCE = "blackmarble-nrt"  # worker/jobs.py LIGHTS_SOURCE


def _night_lights_loaded(engine: Any) -> bool:
    """True once the worker has run the power-loss rule on a night-light history at least once."""
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT last_success_at FROM source_status WHERE id = :s"), {"s": NIGHT_LIGHT_SOURCE}
        ).first()
    return row is not None and row.last_success_at is not None


def build(
    engine: Any,
    identity: Identity,
    area_id: str | None,
    limit: int,
) -> dict[str, Any]:
    """Return the current released, scoped data needed by the map screen."""
    unavailable: dict[str, str] = {
        "shelters": "Validated shelter data is not loaded.",
        "routes": "Validated road and closure data is not loaded.",
    }
    try:
        facility_rows = facilities_real.all_in_scope(engine, identity)
    except facilities_real.NotLoaded:
        facility_rows = None
        # Missing facilities read Unknown on the map, never "0 affected" (D28).
        unavailable["facilities"] = "Validated facility data is not loaded."
    if not _night_lights_loaded(engine):
        unavailable["night_lights"] = (
            "Night-light history is not loaded: possible power loss is Unknown, not zero."
        )

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

    def _one(incident: dict[str, Any]) -> dict[str, Any]:
        """All per-incident reads (several round trips each); run in parallel for remote databases."""
        area = incident["area_id"]
        out: dict[str, Any] = {"id": incident["incident_id"], "area": area}
        out["detail"] = agents_real.get_incident(engine, identity, incident["incident_id"])
        out["damage"] = radar_real.damage(engine, area, None, identity)
        out["budget"] = agents_real.area_budget(engine, area)
        try:
            out["people"] = areas_real.people(engine, area, identity)
        except summary_real.Unavailable:
            out["people_unavailable"] = True
        return out

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_one, incidents["items"]))

    for r in results:
        incident_area = r["area"]
        cell_ids.add(incident_area)
        if r["detail"] is not None:
            details[r["id"]] = r["detail"]
        area_damage = r["damage"]
        damage[incident_area] = area_damage
        if not area_damage["items"]:
            unavailable[f"damage:{incident_area}"] = (
                "No eligible released radar result is available; this is not a zero-impact result."
            )
        cell_ids.update(item["area_id"] for item in area_damage["items"])
        if r["budget"] is not None:
            budgets[incident_area] = r["budget"]
        if r.get("people_unavailable"):
            unavailable[f"people:{incident_area}"] = "Population evidence is not loaded."
        elif r.get("people") is not None:
            people[incident_area] = r["people"]

    cell_ids.update(alert["area_id"] for alert in alerts["items"])
    facilities = _facilities(facility_rows, damage, identity) if facility_rows is not None else None
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
        "facilities": facilities,
        "centroids": _centroids(cell_ids),
        "unavailable": unavailable,
    }


FACILITY_TYPES = ("clinic", "hospital", "school", "water", "power")


def _facilities(rows: list[Any], damage: dict[str, dict[str, Any]], identity: Identity) -> dict[str, Any]:
    """Facility points and per-incident-area counts, from one query and the damage already read.

    Damage status comes from the released r9 results fetched for the incident areas; a facility
    outside those areas is "not assessed in this view", never "undamaged". Points are given to
    roles allowed to see locations (the public viewer is coordinator-level, decision D30)."""
    r9_items = {item["area_id"]: item for area in damage.values() for item in area["items"]}
    show_point = identity.role in facilities_real.LOCATION_ROLES
    items, by_area = [], {}
    for r in rows:
        assessed = r.h3_r8 in damage
        items.append({
            "facility_id": r.facility_id,
            "type": r.type,
            "area_id": r.h3_r9,
            "parent_r8": r.h3_r8,
            "operating_status": "Unknown",
            "damage_status": (facilities_real.damage_status(r9_items.get(r.h3_r9)) if assessed
                              else "Not assessed in this view. Unknown."),
            "label": "Reported",
            "date": r.osm_timestamp.isoformat() if r.osm_timestamp else None,
            "geometry": ({"type": "Point", "coordinates": [round(r.lon, 6), round(r.lat, 6)]}
                         if show_point else None),
        })
        if assessed:
            counts = by_area.setdefault(r.h3_r8, {t: 0 for t in (*FACILITY_TYPES, "total")})
            counts[r.type] = counts.get(r.type, 0) + 1
            counts["total"] += 1
    for area in damage:
        by_area.setdefault(area, {t: 0 for t in (*FACILITY_TYPES, "total")})
    return {"synthetic": False, "source": [facilities_real.SOURCE], "items": items, "by_area": by_area}
