"""Shared test setup: no real database. Real-data mode writes audit rows on sign-in, so every test
gets an in-memory stand-in by default; tests that need richer answers patch their own engine."""

from types import SimpleNamespace

import pytest

from backend.app.api import radar
from backend.app.core import security


class NullEngine:
    """Accepts every write and answers every read with no rows."""

    def __init__(self):
        self.calls = []

    def _execute(self, sql, params=None):
        self.calls.append((str(sql), params or {}))
        return SimpleNamespace(first=lambda: None, all=list, scalar=lambda: None, rowcount=1)

    def _ctx(self):
        engine = self

        class Ctx:
            def __enter__(self):
                return SimpleNamespace(execute=engine._execute)

            def __exit__(self, *a):
                return False
        return Ctx()

    connect = begin = _ctx


@pytest.fixture(autouse=True)
def no_real_database(monkeypatch):
    monkeypatch.setattr(radar, "engine", lambda: NullEngine())
    security._login_failures.clear()
    yield
    security._login_failures.clear()
