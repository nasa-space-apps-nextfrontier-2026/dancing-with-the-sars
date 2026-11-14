import pytest

from backend.app.agents import NAMES, Evidence
from worker.interfaces import SceneManifest, compare_versions, validate_manifest
from worker.main import run_once
from worker.radar import process_gcov, process_gunw


def test_no_invented_measurements():
    result=run_once()
    assert result['status']=='unavailable'
    assert len(result['results'])==len(NAMES)==12
    assert all(row['low'] is None and row['high'] is None and row['label']==Evidence.UNKNOWN for row in result['results'])

def test_version_mismatch_never_claims_damage():
    a=SceneManifest('C3622214170-ASF','2026-01-19','BETA 1.0.2',151,72)
    b=SceneManifest('C2854338529-ASF','2026-06-24','PROVISIONAL 1.0.11',151,72)
    assert not compare_versions(a,b)
    assert process_gcov(a,b).label == Evidence.UNKNOWN
    with pytest.raises(NotImplementedError): process_gunw()
    with pytest.raises(ValueError): validate_manifest(SceneManifest(a.collection_id,a.acquisition_start,a.processing_version,100,72))
