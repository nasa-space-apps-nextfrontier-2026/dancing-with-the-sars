"""Offline, synthetic-only artifact gate. No database writes or HTTP handling."""
import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / 'docs/contracts/openapi.yaml').read_text(encoding='utf-8'))


class ArtifactRejected(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactRejected(message)


def utc(value: object) -> datetime:
    require(isinstance(value, str), 'Acquisition time must be UTC text')
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ArtifactRejected('Invalid acquisition time') from exc
    require(value.endswith('Z') and result.utcoffset().total_seconds() == 0,
            'Acquisition time must use UTC Z')
    return result


def validate_artifact(path: Path) -> dict:
    """Validate a synthetic handoff without ingesting or publishing its contents."""
    manifest = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(manifest, dict), 'Manifest must be an object')
    required = {'schema_version', 'artifact_version', 'synthetic', 'area_id', 'geometry',
                'track', 'frame', 'orbit', 'acquisitions', 'asset', 'classification',
                'source_records', 'layer', 'metric_value'}
    require(set(manifest) == required, 'Manifest fields do not match version 1')
    require(manifest['schema_version'] == '1.0.0' and isinstance(manifest['artifact_version'], str)
            and manifest['artifact_version'], 'Unsupported artifact version')
    require(manifest['synthetic'] is True, 'Only synthetic artifacts accepted by this gate')
    require(manifest['area_id'] == 'demo-area-01' and manifest['geometry'] is None,
            'Synthetic demo has no geographic geometry')
    require(manifest['track'] == 151 and manifest['frame'] == 72
            and manifest['orbit'] == 'descending', 'Unexpected radar scope')
    acquisitions = manifest['acquisitions']
    require(isinstance(acquisitions, list) and len(acquisitions) == 2,
            'Exactly two synthetic acquisition descriptors required')
    times = []
    ids = []
    for acquisition in acquisitions:
        require(isinstance(acquisition, dict) and set(acquisition) == {
            'source_id', 'acquired_at', 'processing_version', 'polarizations',
            'raster_crs', 'valid_pixel_count'}, 'Invalid acquisition descriptor')
        require(isinstance(acquisition['source_id'], str)
                and isinstance(acquisition['processing_version'], str)
                and acquisition['processing_version'], 'Missing source or product version')
        require(acquisition['polarizations'] == ['HH', 'HV']
                and acquisition['raster_crs'] == 'EPSG:4326'
                and acquisition['valid_pixel_count'] == 0,
                'Synthetic input must have declared channels, CRS and zero valid pixels')
        ids.append(acquisition['source_id'])
        times.append(utc(acquisition['acquired_at']))
    require(times[0] < times[1] and len(set(ids)) == 2, 'Invalid acquisition pair')
    require(times[0].date().isoformat() == '2026-01-19'
            and times[1].date().isoformat() == '2026-06-24',
            'Synthetic sample uses only documented window endpoints')
    for name, records in [('SourceRecord', manifest['source_records']),
                          ('Layer', [manifest['layer']]),
                          ('MetricValue', [manifest['metric_value']])]:
        require(isinstance(records, list), f'{name} records must be a list')
        validator = Draft202012Validator({
            'components': SPEC['components'],
            '$ref': f'#/components/schemas/{name}',
        })
        for record in records:
            validator.validate(record)
            require(record['synthetic'] is True, f'{name} must be synthetic')
    sources = manifest['source_records']
    require(len(sources) == 2 and [s['source_id'] for s in sources] == ids,
            'Source records do not match acquisitions')
    for source, acquisition in zip(sources, acquisitions):
        require(source['acquisition_start'] == acquisition['acquired_at']
                and source['processing_version'] == acquisition['processing_version']
                and source['spatial_coverage']['track'] == 151
                and source['spatial_coverage']['frame'] == 72
                and source['live_tested'] is False,
                'Source provenance mismatch')
    layer = manifest['layer']
    value = manifest['metric_value']
    require(layer['source_ids'] == ids and layer['min_role'] != 'public'
            and layer['safety_tag'] == 'restricted_until_review'
            and layer['label'] == 'Unknown', 'Layer release metadata is unsafe')
    require(value['area_id'] == manifest['area_id'] and value['source'] == ids
            and value['metric'] == 'radar_candidate_change'
            and value['low'] is None and value['high'] is None
            and value['label'] == 'Unknown' and value['confidence'] is None,
            'Synthetic no-data value must remain Unknown')
    classification = manifest['classification']
    require(classification == {'class': 'Unknown', 'score': None,
            'reason_codes': ['NO_VALID_PIXELS'], 'qa_status': 'synthetic_test_only'},
            'Synthetic classification cannot claim candidate damage')
    asset = manifest['asset']
    require(isinstance(asset, dict) and set(asset) == {'path', 'format', 'sha256'}
            and asset['format'] == 'CSV', 'Invalid asset metadata')
    relative = Path(asset['path'])
    require(not relative.is_absolute() and '..' not in relative.parts,
            'Asset path must stay beside manifest')
    target = (path.parent / relative).resolve()
    require(target.is_file() and target.parent == path.parent.resolve(),
            'Asset must be a sibling file')
    require(target.stat().st_size <= 65536, 'Synthetic asset is too large')
    require(hashlib.sha256(target.read_bytes()).hexdigest() == asset['sha256'],
            'Asset SHA-256 mismatch')
    with target.open(newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        require(reader.fieldnames == ['area_id', 'before_hh', 'after_hh', 'before_hv',
                                     'after_hv', 'valid_pixels'], 'Unexpected CSV columns')
        rows = list(reader)
    require(rows == [{'area_id': 'demo-area-01', 'before_hh': '', 'after_hh': '',
                     'before_hv': '', 'after_hv': '', 'valid_pixels': '0'}],
            'Synthetic CSV must contain exactly one no-data row')
    return {'area_id': manifest['area_id'], 'sources': ids,
            'classification': 'Unknown', 'synthetic': True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_artifact(args.manifest)))


if __name__ == '__main__':
    main()
