import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

GLOBAL_BLUETOOTH_LOCK: asyncio.Lock = asyncio.Lock()  # type: ignore

RT = TypeVar("RT")


def bluetooth_lock(
    func: Callable[..., Coroutine[Any, Any, RT]]
) -> Callable[..., Coroutine[Any, Any, RT]]:
    """Decorator to lock bluetooth operations."""

    @wraps(func)
    async def wrapped(*args, **kwargs) -> RT:

        async with GLOBAL_BLUETOOTH_LOCK:
            return await func(*args, **kwargs)

    return wrapped
