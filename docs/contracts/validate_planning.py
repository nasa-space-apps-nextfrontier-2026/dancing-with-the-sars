"""Validate planning artifacts only. Does not test an application or scientific data.

Usage: python docs/contracts/validate_planning.py [--validator-path PATH]
Optional packages: openapi-spec-validator and jsonschema (isolated install supported).
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import re
import sys
from urllib.parse import unquote

parser = argparse.ArgumentParser()
parser.add_argument('--validator-path', type=Path)
args = parser.parse_args()
if args.validator_path:
    sys.path.insert(0, str(args.validator_path.resolve()))
D = Path(__file__).resolve().parents[1]
manifest = json.loads((D / 'contracts/planning_manifest.json').read_text(encoding='utf-8'))
errors = []
counts = collections.Counter()

def check(ok, message):
    if not ok:
        errors.append(message)

for filename, expected in manifest['reference_sha256'].items():
    check(hashlib.sha256((D / filename).read_bytes()).hexdigest() == expected,
          'Reference changed: ' + filename)
    counts['unchanged_references'] += 1
for filename in manifest['required_documents']:
    check((D / filename).is_file(), 'Missing required doc: ' + filename)

authored = [p for p in D.rglob('*') if p.is_file() and p.name not in manifest['reference_sha256']
            and '__pycache__' not in p.parts]
for path in authored:
    if path.suffix not in ['.md', '.json', '.yaml', '.py']:
        continue
    text = path.read_text(encoding='utf-8')
    check('\x00' not in text, 'NUL in ' + str(path))
    check(not any(line.rstrip() != line for line in text.splitlines()), 'Trailing whitespace: ' + str(path))
    if path.suffix == '.md':
        counts['markdown_files'] += 1
        check(text.count('```') % 2 == 0, 'Unbalanced code fence: ' + str(path))
        without_code = re.sub(r'```.*?```', '', text, flags=re.S)
        for _, target in re.findall(r'\[([^\]\n]+)\]\(([^)\n]+)\)', without_code):
            if re.match(r'^(https?://|mailto:|#)', target):
                continue
            target = unquote(target.split('#')[0].strip('<>'))
            check((path.parent / target).exists(), f'Broken link in {path.name}: {target}')
            counts['local_links'] += 1
        width = None
        for line in without_code.splitlines():
            if line.startswith('|'):
                cells = len(re.split(r'(?<!\\)\|', line)) - 2
                if width is None:
                    width = cells
                check(cells == width, f'Table column mismatch in {path.name}: {line[:100]}')
                counts['table_rows'] += 1
            else:
                width = None
        for diagram in re.findall(r'```mermaid\s*\n(.*?)```', text, re.S):
            kind = diagram.strip().splitlines()[0].strip()
            check(kind.startswith(('flowchart ', 'sequenceDiagram', 'erDiagram', 'gitGraph')),
                  'Unexpected Mermaid type in ' + path.name)
            counts['mermaid_blocks'] += 1
    if path.suffix in ['.json', '.yaml']:
        try:
            json.loads(text)  # openapi.yaml intentionally uses JSON, valid YAML 1.2.
            counts['json_or_yaml_files'] += 1
        except ValueError as exc:
            errors.append(f'Invalid JSON/YAML {path.name}: {exc}')

task_paths = sorted((D / 'tasks').glob('MEMBER_*.md'))
check(len(task_paths) == 4, 'Exactly four member files required')
task_ids = []
required_fields = ['Source trace', 'Scope', 'Priority / phase', 'Accountable owner', 'One reviewer',
                   'Dependency', 'Expected files / outputs', 'Required stub / mock',
                   'Effort and hackathon window', 'Input / output contract', 'Local verification (planned)',
                   'Test cases', 'Definition of Done', 'Integration checkpoint', 'Blockers / fallback']
for path in task_paths:
    sections = re.split(r'^## (M[1-4]-\d{2}):', path.read_text(encoding='utf-8'), flags=re.M)
    for i in range(1, len(sections), 2):
        task_id, body = sections[i:i + 2]
        task_ids.append(task_id)
        for field in required_fields:
            check(f'| {field} |' in body, f'{task_id}: missing {field}')
        owner = re.search(r'\| Accountable owner \| (Member [1-4]) \|', body)
        reviewer = re.search(r'\| One reviewer \| (Member [1-4]) \|', body)
        check(bool(owner and reviewer and owner[1] != reviewer[1]), task_id + ': owner/reviewer invalid')
check(sorted(task_ids) == sorted(manifest['task_ids']), 'Task ID inventory mismatch')
check(len(task_ids) == len(set(task_ids)), 'Duplicate task IDs')
counts['tasks'] = len(task_ids)

trace = (D / '14_REQUIREMENTS_TRACEABILITY_MATRIX.md').read_text(encoding='utf-8')
row_ids = re.findall(r'^\| ((?:F\d+|UI-[SC]\d+|API-\d+|DS\d+|A\d+|X\d+|AG-\d+|T-[A-Z0-9]+|D\d+|OUT-\d+|PDF-\d+|SRC-\d+-\d+)) \|', trace, re.M)
check(len(row_ids) == len(set(row_ids)), 'Duplicate trace IDs')
check(set(row_ids) == set(manifest['trace_ids']), 'Trace inventory mismatch')
counts['trace_rows'] = len(row_ids)
for name in manifest['screens'] + manifest['components'] + manifest['agents']:
    check(name in trace, 'Unmapped named item: ' + name)
for row in trace.splitlines():
    if row.startswith('| ') and re.search(r'\| M[1-4]-\d{2} \|', row):
        task_id = re.search(r'\| (M[1-4]-\d{2}) \|', row)[1]
        check(task_id in task_ids, 'Trace references unknown task: ' + task_id)

# Recompute source statement selection independently from the saved line inventory.
for filename, expected_lines in manifest['source_statement_lines'].items():
    lines = (D / filename).read_text(encoding='utf-8').splitlines()
    actual = []
    code = False
    for number, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('```'):
            code = not code
            continue
        if code or not s or s.startswith('#') or re.fullmatch(r'[-\s]+', s):
            continue
        if s.startswith('|') and (re.fullmatch(r'[|:\-\s]+', s)
                                 or (number < len(lines) and re.fullmatch(r'[|:\-\s]+', lines[number].strip()))):
            continue
        actual.append(number)
    check(actual == expected_lines, 'Source statement coverage differs: ' + filename)
    counts['source_statements'] += len(actual)

spec = json.loads((D / 'contracts/openapi.yaml').read_text(encoding='utf-8'))
operations = []
for path, methods in spec['paths'].items():
    for method, op in methods.items():
        operations.append(op)
        check(op.get('x-owner-task') in task_ids, 'Unknown API owner: ' + path)
        check({'401', '403', '422', '429'}.issubset(op['responses']), 'Missing error contract: ' + path)
        check(set(re.findall(r'\{(\w+)\}', path)) ==
              {p['name'] for p in op['parameters'] if p['in'] == 'path'}, 'Path parameter mismatch: ' + path)
check(len(operations) == manifest['endpoint_count'], 'Endpoint count mismatch')
counts['api_operations'] = len(operations)
check(len({op['operationId'] for op in operations}) == len(operations), 'Duplicate operationId')

for path in (D / 'contracts').glob('*.json'):
    if path.name == 'planning_manifest.json':
        continue
    example = json.loads(path.read_text(encoding='utf-8'))
    check(example.get('synthetic') is True, 'Missing synthetic flag: ' + path.name)
    def inspect(value, location='root'):
        if isinstance(value, dict):
            if 'low' in value and 'high' in value and value['low'] is not None and value['high'] is not None:
                check(value['low'] <= value['high'], f'Reversed range {path.name}/{location}')
            for key, val in value.items():
                if key in ['geometry', 'coordinates', 'latitude', 'longitude']:
                    check(val is None, f'Sensitive location in fixture {path.name}/{location}')
                inspect(val, location + '.' + key)
        elif isinstance(value, list):
            for val in value:
                inspect(val, location + '[]')
    inspect(example)
    counts['synthetic_examples'] += 1

formal = 'not run: install optional validators or pass --validator-path'
try:
    from openapi_spec_validator import validate
    from jsonschema import Draft202012Validator
    validate(spec)
    schemas = spec['components']['schemas']
    def resolved(schema):
        if isinstance(schema, dict):
            if '$ref' in schema:
                return resolved(schemas[schema['$ref'].rsplit('/', 1)[-1]])
            return {k: resolved(v) for k, v in schema.items()}
        if isinstance(schema, list):
            return [resolved(v) for v in schema]
        return schema
    for op in operations:
        for response in op['responses'].values():
            for content in response.get('content', {}).values():
                if 'example' in content:
                    Draft202012Validator(resolved(content['schema'])).validate(content['example'])
                    counts['validated_response_examples'] += 1
        for content in op.get('requestBody', {}).get('content', {}).values():
            Draft202012Validator(resolved(content['schema'])).validate(content['example'])
            counts['validated_request_examples'] += 1
    for path in (D / 'contracts').glob('*.json'):
        if path.stem in schemas:
            Draft202012Validator(resolved(schemas[path.stem])).validate(json.loads(path.read_text(encoding='utf-8')))
    formal = 'passed: OpenAPI specification and JSON Schema examples; no live server'
except ImportError:
    pass
except Exception as exc:
    errors.append('Formal schema validation: ' + str(exc))

# Targeted token/private-key scan, not a guarantee against every possible secret format.
secret_patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                   r'gh[pousr]_[A-Za-z0-9]{30,}', r'AKIA[0-9A-Z]{16}',
                   r'sk-(?:proj-)?[A-Za-z0-9_-]{35,}']
for path in authored:
    if path.suffix in ['.md', '.json', '.yaml']:
        text = path.read_text(encoding='utf-8')
        for pattern in secret_patterns:
            check(not re.search(pattern, text), 'Potential secret in ' + path.name)

result = {'status': 'PASS' if not errors else 'FAIL', 'counts': dict(counts),
          'formal_schema_validation': formal,
          'mermaid_validation': 'structure only in this script; renderer/parser verification separate',
          'errors': errors}
print(json.dumps(result, indent=2))
raise SystemExit(1 if errors else 0)
