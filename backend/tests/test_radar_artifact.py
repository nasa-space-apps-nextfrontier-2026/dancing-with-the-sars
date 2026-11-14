import json
import shutil
from pathlib import Path

import pytest
from scripts.ingest_radar_artifact import ArtifactRejected, validate_artifact

FIXTURES = Path(__file__).resolve().parents[2] / 'shared/fixtures'


def sample(tmp_path):
    for name in ('synthetic_radar_manifest.json', 'synthetic_radar_features.csv'):
        shutil.copyfile(FIXTURES / name, tmp_path / name)
    return tmp_path / 'synthetic_radar_manifest.json'


def test_synthetic_artifact_passes_offline_gate(tmp_path):
    result = validate_artifact(sample(tmp_path))
    assert result == {'area_id': 'demo-area-01',
                      'sources': ['demo-source-01', 'demo-source-02'],
                      'classification': 'Unknown', 'synthetic': True}


@pytest.mark.parametrize('change', [
    lambda m: m.update(synthetic=False),
    lambda m: m.update(schema_version='2.0.0'),
    lambda m: m['asset'].update(sha256='0' * 64),
    lambda m: m['layer'].update(min_role='public'),
    lambda m: m['metric_value'].update(low=0, high=1),
    lambda m: m['classification'].update({'class': 'candidate_change'}),
    lambda m: m['acquisitions'][1].update(acquired_at='2026-03-01T00:00:00Z'),
])
def test_artifact_rejects_unsafe_or_unverifiable_input(tmp_path, change):
    path = sample(tmp_path)
    manifest = json.loads(path.read_text())
    change(manifest)
    path.write_text(json.dumps(manifest))
    with pytest.raises((ArtifactRejected, ValueError)):
        validate_artifact(path)
