from collections.abc import Callable

HANDLERS: dict[tuple[str, str], Callable] = {}

def handler(method: str, path: str):
    def decorator(fn: Callable):
        HANDLERS[(method.upper(), path)] = fn
        return fn
    return decorator

# Import handler modules to register them
from . import (
    areas,  # noqa: F401
    sources,  # noqa: F401
)
