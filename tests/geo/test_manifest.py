"""M1-01 manifest tests on synthetic ASF metadata (no network, no real scenes)."""

import pytest

from pipelines.radar.nisar.discover import (
    assign_tier,
    build_manifest,
    load_config,
    maturity_of,
    missing_passes,
)

CFG = load_config()


def feature(date, product="GCOV", collection="NISAR_L2_GCOV_PROVISIONAL_V1", crid="P05023",
            track=151, frame=72, processed="2026-07-01T00:00:00Z", size=1_780_000_000):
    scene = f"NISAR_L2_PR_{product}_{track}_{frame}_{date.replace('-', '')}_{crid}_{processed[:10]}"
    return {
        "properties": {
            "sceneName": scene, "fileName": f"{scene}.h5", "bytes": {f"{scene}.h5": {"bytes": size}},
            "processingLevel": product, "collectionName": collection, "conceptID": "C-TEST",
            "crid": crid, "pgeVersion": "R05", "pathNumber": track, "frameNumber": frame,
            "flightDirection": "DESCENDING", "startTime": f"{date}T16:25:10Z",
            "stopTime": f"{date}T16:25:45Z", "processingDate": processed, "frameCoverage": "Full",
            "rangeBandwidth": ["20+5"], "mainBandPolarization": ["HH", "HV"], "url": f"https://x/{scene}.h5",
        },
        "geometry": None,
    }


def test_maturity_names():
    assert maturity_of("NISAR_L2_GCOV_BETA_V1") == "BETA"
    assert maturity_of("NISAR_L2_GCOV_PROVISIONAL_V1") == "PROVISIONAL"
    assert maturity_of("NISAR_L2_GCOV_V1") == "V1"
    with pytest.raises(ValueError):
        maturity_of("SOMETHING_ELSE")


def test_tiers():
    rec = {"product": "GCOV", "date": "2026-01-19"}
    assert assign_tier(rec, CFG) == "A-before"
    assert assign_tier({"product": "GCOV", "date": "2026-06-24"}, CFG) == "A-after"
    assert assign_tier({"product": "GCOV", "date": "2026-11-03"}, CFG) == "B"
    assert assign_tier({"product": "GSLC", "date": "2026-01-19"}, CFG) == "C"
    assert assign_tier({"product": "GSLC", "date": "2026-07-06"}, CFG) is None


def test_gap_is_kept_not_filled():
    assert missing_passes(["2026-01-07", "2026-01-31"]) == ["2026-01-19"]
    assert missing_passes([]) == []


def test_wrong_track_rejected_and_duplicates_kept():
    feats = [
        feature("2026-01-19", collection="NISAR_L2_GCOV_BETA_V1", crid="X05010"),
        feature("2026-06-24"),
        feature("2026-09-04", processed="2026-09-10T00:00:00Z"),
        feature("2026-09-04", processed="2026-10-01T00:00:00Z"),
        feature("2026-06-24", track=100),
    ]
    m = build_manifest(feats, CFG)
    assert m["rejected_other_tracks"] == 1
    sep = next(s for s in m["scenes"] if s["date"] == "2026-09-04")
    assert sep["selected"]["processing_date"].startswith("2026-10-01")
    assert len(sep["other_versions"]) == 1
    assert any(w.startswith("version_confounded") for w in m["warnings"])


def test_higher_maturity_wins():
    feats = [
        feature("2026-10-22", collection="NISAR_L2_GCOV_PROVISIONAL_V1", processed="2026-11-01T00:00:00Z"),
        feature("2026-10-22", collection="NISAR_L2_GCOV_V1", crid="P05036", processed="2026-10-30T00:00:00Z"),
    ]
    m = build_manifest(feats, CFG)
    assert m["scenes"][0]["selected"]["maturity"] == "V1"


def test_manifest_has_run_id_and_tier_bytes():
    m = build_manifest([feature("2026-06-24"), feature("2026-07-06")], CFG)
    assert len(m["run_id"]) == 16
    assert m["tiers"]["A-after"] == {"scenes": 2, "bytes": 2 * 1_780_000_000}
