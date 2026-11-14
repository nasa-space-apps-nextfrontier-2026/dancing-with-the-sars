"""Area scopes. A user's scope covers the named area and every area inside it.

Scope ids:
  demo-area-01          the synthetic fixture area (exact match only)
  south-lebanon-demo    the real demo box: covers every H3 cell whose centre is inside it
  <H3 cell id>          covers that cell and its finer children (for example r8 -> its r9 cells)
"""

from __future__ import annotations

import h3

DEMO_BOX = {"west": 35.0, "south": 33.0, "east": 36.0, "north": 33.6}  # docs/DATA_AND_API_PLAN.md
AOI_ID = "south-lebanon-demo"


def _is_cell(value: str) -> bool:
    try:
        return h3.is_valid_cell(value)
    except (TypeError, ValueError):
        return False


def in_demo_box(cell: str) -> bool:
    lat, lng = h3.cell_to_latlng(cell)
    return DEMO_BOX["south"] <= lat <= DEMO_BOX["north"] and DEMO_BOX["west"] <= lng <= DEMO_BOX["east"]


def area_in_scope(area_id: str, scopes: tuple[str, ...] | list[str]) -> bool:
    if area_id in scopes:
        return True
    if not _is_cell(area_id):
        return False
    res = h3.get_resolution(area_id)
    for scope in scopes:
        if scope == AOI_ID and in_demo_box(area_id):
            return True
        if _is_cell(scope) and h3.get_resolution(scope) < res and h3.cell_to_parent(area_id, h3.get_resolution(scope)) == scope:
            return True
    return False
