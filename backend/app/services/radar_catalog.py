"""Read-only adapter for the reviewed synthetic radar handoff contract.

The fixture contains catalogue metadata only: no pixels and no geometry.  Keeping
that distinction in this adapter prevents the UI from treating an acquisition
date as a renderable observation.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / 'shared' / 'fixtures' / 'synthetic_radar_manifest.json'
DEMO_AREA_ID = 'demo-area-01'
DEMO_LAYER_ID = 'demo-damage-r8'


def _manifest() -> dict:
    payload = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    if payload.get('synthetic') is not True or payload.get('area_id') != DEMO_AREA_ID:
        raise ValueError('Radar fixture is not the reviewed synthetic handoff')
    return payload


def layer_catalog() -> list[dict]:
    """Return the reviewed layer metadata without adding renderable assets."""
    return [_manifest()['layer']]


def observation_series(layer_id: str, area_id: str | None) -> dict | None:
    """Return exact catalogue acquisitions for the supported demo area/layer."""
    if layer_id != DEMO_LAYER_ID or area_id != DEMO_AREA_ID:
        return None
    manifest = _manifest()
    classification = manifest['classification']
    observations = []
    for index, acquisition in enumerate(manifest['acquisitions']):
        version = acquisition['processing_version']
        observations.append({
            'observation_id': f"{layer_id}-{index + 1}",
            **acquisition,
            'product_maturity': 'provisional' if 'PROVISIONAL' in version else 'beta',
            'raster_available': False,
            'qa_status': classification['qa_status'],
            'evidence_label': classification['class'],
            'limitations': [
                'No raster pixels or geometry are present in this contract fixture.',
                'The acquisition is catalogue metadata, not a validated NISAR observation.',
            ],
        })
    return {
        'synthetic': True,
        'layer_id': layer_id,
        'area_id': area_id,
        'track': manifest['track'],
        'frame': manifest['frame'],
        'orbit': manifest['orbit'],
        'points': observations,
        'missing_intervals': manifest['layer']['missing_intervals'],
    }
