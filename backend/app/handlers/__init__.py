from collections.abc import Callable

HANDLERS: dict[tuple[str, str], Callable] = {}

def handler(method: str, path: str):
    def decorator(fn: Callable):
        HANDLERS[(method.upper(), path)] = fn
        return fn
    return decorator