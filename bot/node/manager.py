from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional
from uuid import UUID

from loguru import logger

from .models import NodeInfo, NodeStatus, Task, TaskResult, TaskResultRequest

HEARTBEAT_TIMEOUT = timedelta(minutes=5)
_DEFAULT_STORE = Path("nodes.json")


class NodeManager:
    """Registry for nodes and tasks.

    Node registrations are persisted to a JSON file so they survive host
    restarts.  Tasks are intentionally kept in-memory only — they are
    short-lived and tied to a specific Telegram message that would be stale
    after a restart anyway.
    """

    def __init__(self, store: Path = _DEFAULT_STORE) -> None:
        self._store = store
        self._nodes: dict[str, NodeInfo] = {}
        self._tasks: dict[UUID, Task] = {}
        self._results: dict[UUID, list[TaskResult]] = {}
        self._result_callbacks: dict[
            UUID, list[Callable[[Task, TaskResult], Coroutine[Any, Any, None]]]
        ] = {}
        self._checker_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load persisted node registrations from disk (called once on start)."""
        if not self._store.exists():
            logger.info(f"No node store found at {self._store}, starting fresh.")
            return
        try:
            raw: list[dict] = json.loads(self._store.read_text(encoding="utf-8"))
            for entry in raw:
                node = NodeInfo.model_validate(entry)
                # Nodes loaded from disk are considered offline until they
                # send a heartbeat — we don't know if they're still alive.
                node.status = NodeStatus.OFFLINE
                self._nodes[node.name] = node
            logger.info(
                f"Loaded {len(self._nodes)} node(s) from {self._store}: "
                + ", ".join(self._nodes)
            )
        except Exception as exc:
            logger.error(f"Failed to load node store ({self._store}): {exc}")

    def _save(self) -> None:
        """Persist current node registrations to disk."""
        try:
            data = [n.model_dump(mode="json") for n in self._nodes.values()]
            self._store.write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:
            logger.error(f"Failed to save node store ({self._store}): {exc}")

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._load()
        self._checker_task = asyncio.create_task(self._heartbeat_checker())

    def stop(self) -> None:
        if self._checker_task:
            self._checker_task.cancel()

    async def _heartbeat_checker(self) -> None:
        while True:
            await asyncio.sleep(60)
            now = datetime.now(timezone.utc)
            changed = False
            for node in self._nodes.values():
                if node.status == NodeStatus.ONLINE:
                    if now - node.last_heartbeat > HEARTBEAT_TIMEOUT:
                        node.status = NodeStatus.OFFLINE
                        changed = True
                        logger.warning(
                            f"Node {node.name!r} went offline (no heartbeat)"
                        )
            # Persist status changes so the offline state survives a restart too
            if changed:
                self._save()

    # ── Nodes ─────────────────────────────────────────────────────────────────

    def register_node(self, name: str, ip: str) -> NodeInfo:
        if name in self._nodes:
            node = self._nodes[name]
            node.ip = ip
            node.status = NodeStatus.ONLINE
            node.last_heartbeat = datetime.now(timezone.utc)
            logger.info(f"Node {name!r} re-registered from {ip}")
        else:
            node = NodeInfo(name=name, ip=ip)
            self._nodes[name] = node
            logger.info(f"Node {name!r} registered from {ip}")
        self._save()
        return node

    def heartbeat(self, name: str) -> bool:
        """Update heartbeat timestamp.

        Returns ``False`` if the node is not registered so the caller can send
        back a 404 — the client should then re-register itself.
        """
        if name not in self._nodes:
            return False
        node = self._nodes[name]
        was_offline = node.status == NodeStatus.OFFLINE
        node.last_heartbeat = datetime.now(timezone.utc)
        node.status = NodeStatus.ONLINE
        # Heartbeats arrive frequently; we only persist when the status flips
        # from OFFLINE → ONLINE to avoid hammering the disk every few seconds.
        if was_offline:
            self._save()
        return True

    def get_nodes(self) -> list[NodeInfo]:
        return list(self._nodes.values())

    def get_online_nodes(self) -> list[str]:
        return [n.name for n in self._nodes.values() if n.status == NodeStatus.ONLINE]

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def create_task(self, task: Task) -> Task:
        task.target_nodes = self.get_online_nodes()
        self._tasks[task.id] = task
        self._results[task.id] = []
        logger.info(f"Task {task.id} created, targeting nodes: {task.target_nodes}")
        return task

    def get_pending_tasks_for_node(self, node_name: str) -> list[Task]:
        """Return tasks that target this node and haven't been responded to yet."""
        return [
            task
            for task in self._tasks.values()
            if node_name in task.target_nodes and node_name not in task.client
        ]

    def submit_result(
        self, task_id: UUID, node_name: str, body: TaskResultRequest
    ) -> bool:
        """Record a result from a node. Returns ``False`` if task not found."""
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]
        if node_name not in task.client:
            task.client.append(node_name)

        result = TaskResult(
            task_id=task_id,
            node_name=node_name,
            success=body.success,
            result=body.result,
            error=body.error,
            elapsed_ms=body.elapsed_ms,
        )
        self._results[task_id].append(result)
        logger.info(
            f"Task {task_id}: result from {node_name!r} (success={body.success})"
        )

        if task_id in self._result_callbacks:
            for cb in self._result_callbacks[task_id]:
                asyncio.create_task(cb(task, result))

        return True

    def get_task(self, task_id: UUID) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_results(self, task_id: UUID) -> list[TaskResult]:
        return self._results.get(task_id, [])

    def register_result_callback(
        self,
        task_id: UUID,
        cb: Callable[[Task, TaskResult], Coroutine[Any, Any, None]],
    ) -> None:
        self._result_callbacks.setdefault(task_id, []).append(cb)

    def remove_task(self, task_id: UUID) -> None:
        self._tasks.pop(task_id, None)
        self._results.pop(task_id, None)
        self._result_callbacks.pop(task_id, None)


# Singleton instance shared across the process
manager = NodeManager()
