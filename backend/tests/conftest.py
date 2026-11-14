"""No real database in unit tests: reuse the in-memory stand-in from tests/security."""
from tests.security.conftest import no_real_database  # noqa: F401
