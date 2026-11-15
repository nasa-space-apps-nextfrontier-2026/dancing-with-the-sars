import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from .config import get_settings

SESSION_SECONDS = 8 * 60 * 60
_sessions: dict[str, tuple["Identity", float, str]] = {}

@dataclass(frozen=True)
class Identity:
    user_id: str
    role: str
    area_scopes: tuple[str, ...]

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    rounds = 310_000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, rounds)
    return f'pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 200_000 <= int(rounds) <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def authenticate(username: str, password: str) -> Identity | None:
    try:
        entry = json.loads(get_settings().civisar_demo_users_json).get(username)
    except (ValueError, TypeError):
        return None
    if not isinstance(entry, dict) or not verify_password(password, entry.get('password_hash', '')):
        return None
    role = entry.get('role')
    if role not in ('analyst', 'officer', 'coordinator', 'admin'):
        return None
    scopes = entry.get('area_scopes', [])
    if not isinstance(scopes, list) or not all(isinstance(x, str) for x in scopes):
        return None
    return Identity(username, role, tuple(scopes))

def issue_session(identity: Identity) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    _sessions[hashlib.sha256(token.encode()).hexdigest()] = (identity, time.time() + SESSION_SECONDS, csrf)
    return token, csrf

def read_session(token: str | None) -> tuple[Identity, str] | None:
    if not token:
        return None
    key = hashlib.sha256(token.encode()).hexdigest()
    item = _sessions.get(key)
    if not item:
        return None
    identity, expiry, csrf = item
    if expiry <= time.time():
        _sessions.pop(key, None)
        return None
    return identity, csrf

def revoke_session(token: str | None) -> None:
    if token:
        _sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)

def revoke_user(user_id: str) -> int:
    """End every session of one user (used after a role change)."""
    keys = [k for k, (identity, _, _) in _sessions.items() if identity.user_id == user_id]
    for k in keys:
        _sessions.pop(k, None)
    return len(keys)

# Login rate limit (doc 07): 5 failures per username + client in 15 minutes -> wait.
LOGIN_WINDOW = 15 * 60
LOGIN_MAX_FAILURES = 5
_login_failures: dict[str, list[float]] = {}

def login_retry_after(key: str) -> int | None:
    now = time.time()
    recent = [t for t in _login_failures.get(key, []) if t > now - LOGIN_WINDOW]
    _login_failures[key] = recent
    if len(recent) >= LOGIN_MAX_FAILURES:
        return int(recent[0] + LOGIN_WINDOW - now) + 1
    return None

def note_login_failure(key: str) -> None:
    _login_failures.setdefault(key, []).append(time.time())

def clear_login_failures(key: str) -> None:
    _login_failures.pop(key, None)
