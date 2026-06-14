"""LangGraph Async SQLite Checkpointer。"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from storage.db import get_db_path, init_db

if TYPE_CHECKING:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_stack: AsyncExitStack | None = None
_checkpointer: AsyncSqliteSaver | None = None


async def init_checkpointer():
    global _stack, _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    init_db()
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    path = str(get_db_path())
    _stack = AsyncExitStack()
    saver = await _stack.enter_async_context(AsyncSqliteSaver.from_conn_string(path))
    await saver.setup()
    _checkpointer = saver
    return _checkpointer


async def close_checkpointer() -> None:
    global _stack, _checkpointer
    if _stack is not None:
        await _stack.aclose()
    _stack = None
    _checkpointer = None


def get_checkpointer() -> AsyncSqliteSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized — call init_checkpointer() at startup")
    return _checkpointer
