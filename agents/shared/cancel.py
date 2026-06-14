"""运行中任务取消标记（thread_id / task_id）。"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_cancelled_threads: set[str] = set()
_cancelled_tasks: set[str] = set()


def mark_cancelled(*, thread_id: str = "", task_id: str = "") -> None:
    with _lock:
        if thread_id:
            _cancelled_threads.add(thread_id)
        if task_id:
            _cancelled_tasks.add(task_id)


def is_cancelled(*, thread_id: str = "", task_id: str = "") -> bool:
    with _lock:
        if thread_id and thread_id in _cancelled_threads:
            return True
        if task_id and task_id in _cancelled_tasks:
            return True
    return False


def clear_cancelled(*, thread_id: str = "", task_id: str = "") -> None:
    with _lock:
        if thread_id:
            _cancelled_threads.discard(thread_id)
        if task_id:
            _cancelled_tasks.discard(task_id)
