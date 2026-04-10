from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Coroutine, Optional
from uuid import UUID

from loguru import logger

from .models import NodeInfo, NodeStatus, Task, TaskResult, TaskResultRequest

HEARTBEAT_TIMEOUT = timedelta(minutes=5)


class NodeManager:
    """In-memory registry for nodes and tasks."""

    def __init__(self) -> None:
        self._nodes: dict[str, NodeInfo] = {}
        self._tasks: dict[UUID, Task] = {}
        self._results: dict[UUID, list[TaskResult]] = {}
        # Callbacks called when a task result arrives: task_id → list of callbacks
        self._result_callbacks: dict[
            UUID, list[Callable[[Task, TaskResult], Coroutine[Any, Any, None]]]
        ] = {}
        self._checker_task: Optional[asyncio.Task] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._checker_task = asyncio.create_task(self._heartbeat_checker())

    def stop(self) -> None:
        if self._checker_task:
            self._checker_task.cancel()

    async def _heartbeat_checker(self) -> None:
        while True:
            await asyncio.sleep(60)
            now = datetime.now(timezone.utc)
            for node in self._nodes.values():
                if node.status == NodeStatus.ONLINE:
                    if now - node.last_heartbeat > HEARTBEAT_TIMEOUT:
                        node.status = NodeStatus.OFFLINE
                        logger.warning(
                            f"Node {node.name!r} went offline (no heartbeat)"
                        )

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
        return node

    def heartbeat(self, name: str) -> bool:
        """Update heartbeat. Returns False if node not found."""
        if name not in self._nodes:
            return False
        node = self._nodes[name]
        node.last_heartbeat = datetime.now(timezone.utc)
        node.status = NodeStatus.ONLINE
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
        pending = []
        for task in self._tasks.values():
            if node_name in task.target_nodes and node_name not in task.client:
                pending.append(task)
        return pending

    def submit_result(
        self, task_id: UUID, node_name: str, body: TaskResultRequest
    ) -> bool:
        """Record a result from a node. Returns False if task not found."""
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

        # fire callbacks
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
