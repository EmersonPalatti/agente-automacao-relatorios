from __future__ import annotations

import logging
from contextvars import ContextVar
from collections.abc import Callable

log = logging.getLogger("data_agent")

_cb: ContextVar[Callable[[str], None] | None] = ContextVar("pipeline_progress", default=None)


def set_progress(fn: Callable[[str], None] | None):
    return _cb.set(fn)


def reset_progress(token) -> None:
    _cb.reset(token)


def emit(msg: str) -> None:
    log.info(msg)
    fn = _cb.get()
    if fn is not None:
        fn(msg)
