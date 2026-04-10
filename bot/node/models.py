from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DNSQueryType(str, Enum):
    UDP = "UDP"
    DOH = "DOH"
    DOT = "DOT"
    DOQ = "DOQ"


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


# ── Node ──────────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    name: str
    ip: str


class NodeInfo(BaseModel):
    name: str
    ip: str
    status: NodeStatus = NodeStatus.ONLINE
    last_heartbeat: datetime = Field(default_factory=_utcnow)
    registered_at: datetime = Field(default_factory=_utcnow)


# ── Task ──────────────────────────────────────────────────────────────────────


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    action: str = "query"
    type: DNSQueryType
    server: str
    query: str
    record_type: str = "A"
    client: list[str] = Field(default_factory=list)  # nodes that have responded
    target_nodes: list[str] = Field(
        default_factory=list
    )  # all online nodes at creation
    created_at: datetime = Field(default_factory=_utcnow)
    # Internal Telegram context (not exposed to clients)
    chat_id: Optional[int] = None
    message_id: Optional[int] = None

    def to_client_dict(self) -> dict:
        """Return only the fields relevant to client nodes."""
        return {
            "id": str(self.id),
            "action": self.action,
            "type": self.type.value,
            "server": self.server,
            "query": self.query,
            "record_type": self.record_type,
            "client": self.client,
        }


class TaskResult(BaseModel):
    task_id: UUID
    node_name: str
    success: bool
    result: Optional[Any] = None  # raw result data from client
    error: Optional[str] = None
    elapsed_ms: float
    responded_at: datetime = Field(default_factory=_utcnow)


class TaskResultRequest(BaseModel):
    """Body sent by client nodes when posting a result."""

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    elapsed_ms: float


# ── API responses ─────────────────────────────────────────────────────────────


class StatusResponse(BaseModel):
    status: str = "ok"


class RegisterResponse(BaseModel):
    status: str = "ok"
    name: str
