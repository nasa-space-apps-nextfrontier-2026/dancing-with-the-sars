"""Reject obvious credential material in versioned project files.

This is a narrow CI guard, not a substitute for a dedicated secret scanner.
"""
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root)
paths = [Path(item.decode('utf-8')) for item in tracked.split(b'\0') if item]
patterns = [re.compile('BEGIN ' + '(?:RSA |EC |OPENSSH )?' + 'PRIVATE KEY'),
            re.compile('ghp_' + '[A-Za-z0-9]{36}'),
            re.compile('sk-' + '[A-Za-z0-9]{30,}')]
findings = []
for path in paths:
    if path == Path('scripts/check_secrets.py') or not (root / path).is_file():
        continue
    if path.name == '.env' or path.suffix in {'.pem', '.key'}:
        findings.append(str(path))
        continue
    if (root / path).stat().st_size > 2_000_000:
        continue
    content = (root / path).read_text(encoding='utf-8', errors='ignore')
    if any(pattern.search(content) for pattern in patterns):
        findings.append(str(path))
if findings:
    raise SystemExit('Potential secrets: ' + ', '.join(findings))
print('PASS: no obvious credentials in project files')
