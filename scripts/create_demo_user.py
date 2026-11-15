"""Create a local synthetic demo account in ignored .env; no default password ships."""
import json
import re
from getpass import getpass
from pathlib import Path

from backend.app.core.security import hash_password

root = Path(__file__).resolve().parents[1]
env = root / '.env'
text = env.read_text(encoding='utf-8') if env.exists() else (root / '.env.example').read_text(encoding='utf-8')
match = re.search(r'^CIVISAR_DEMO_USERS_JSON=(.*)$', text, re.MULTILINE)
users = json.loads(match.group(1)) if match else {}
username = input('Demo username: ').strip()
role = input('Role (analyst/officer/coordinator/admin): ').strip()
if not username or role not in {'analyst', 'officer', 'coordinator', 'admin'}:
    raise SystemExit('A username and one listed role are required')
default_scopes = 'demo-area-01,south-lebanon-demo'
scopes_text = input(f'Area scopes, comma-separated [{default_scopes}]: ').strip() or default_scopes
scopes = [s.strip() for s in scopes_text.split(',') if s.strip()]
password = getpass('New local password: ')
if len(password) < 12:
    raise SystemExit('Use at least 12 characters')
# demo-area-01 = synthetic fixtures; south-lebanon-demo = real data inside the demo box
users[username] = {'password_hash': hash_password(password), 'role': role, 'area_scopes': scopes}
value = 'CIVISAR_DEMO_USERS_JSON=' + json.dumps(users, separators=(',', ':'))
text = re.sub(r'^CIVISAR_DEMO_USERS_JSON=.*$', lambda _: value, text, flags=re.MULTILINE) if match else text + '\n' + value + '\n'
env.write_text(text, encoding='utf-8')
print('Local demo account saved to ignored .env')
