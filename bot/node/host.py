from __future__ import annotations

from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .manager import manager
from .models import (
    RegisterRequest,
    RegisterResponse,
    StatusResponse,
    TaskResultRequest,
)

_bearer = HTTPBearer(auto_error=True)


def _auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> None:
    """Dependency: validate Bearer token against configured auth_token."""
    from bot.config import get_config

    token = get_config().node.host.auth_token
    if credentials.credentials != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def create_app() -> FastAPI:
    app = FastAPI(title="DecaJoins Node Hub", version="1.0.0")

    # ── Node registration ──────────────────────────────────────────────────────

    @app.post(
        "/api/nodes/register",
        response_model=RegisterResponse,
        dependencies=[Depends(_auth)],
    )
    async def register_node(body: RegisterRequest) -> RegisterResponse:
        node = manager.register_node(body.name, body.ip)
        return RegisterResponse(name=node.name)

    @app.post(
        "/api/nodes/heartbeat",
        response_model=StatusResponse,
        dependencies=[Depends(_auth)],
    )
    async def heartbeat(
        x_node_name: str = Header(..., alias="X-Node-Name"),
    ) -> StatusResponse:
        ok = manager.heartbeat(x_node_name)
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"Node {x_node_name!r} not registered",
            )
        return StatusResponse()

    @app.get("/api/nodes", dependencies=[Depends(_auth)])
    async def list_nodes() -> list[dict]:
        return [n.model_dump(mode="json") for n in manager.get_nodes()]

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @app.get("/api/tasks/pending", dependencies=[Depends(_auth)])
    async def get_pending_tasks(
        x_node_name: str = Header(..., alias="X-Node-Name"),
    ) -> list[dict]:
        tasks = manager.get_pending_tasks_for_node(x_node_name)
        return [t.to_client_dict() for t in tasks]

    @app.post(
        "/api/tasks/{task_id}/result",
        response_model=StatusResponse,
        dependencies=[Depends(_auth)],
    )
    async def submit_result(
        task_id: UUID,
        body: TaskResultRequest,
        x_node_name: str = Header(..., alias="X-Node-Name"),
    ) -> StatusResponse:
        ok = manager.submit_result(task_id, x_node_name, body)
        if not ok:
            raise HTTPException(status_code=404, detail="Task not found")
        return StatusResponse()

    @app.get("/api/tasks/{task_id}", dependencies=[Depends(_auth)])
    async def get_task(task_id: UUID) -> dict:
        task = manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        results = manager.get_results(task_id)
        return {
            "task": task.to_client_dict(),
            "results": [r.model_dump(mode="json") for r in results],
        }

    return app
