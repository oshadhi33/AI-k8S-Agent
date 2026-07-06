from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from insforge_client import insforge
from services.investigation_service import run_full_investigation, stream_investigation

router = APIRouter(prefix="/investigations", tags=["investigations"])


class InvestigateRequest(BaseModel):
    namespace: str = "default"
    target_pod: str | None = None
    incident_title: str | None = None


async def get_user_token(authorization: str | None = Header(default=None)) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        session = await insforge.verify_session(token)
        if session:
            return token
    return None


@router.post("")
async def start_investigation(
    body: InvestigateRequest,
    user_token: str | None = Depends(get_user_token),
):
    try:
        result = await run_full_investigation(
            namespace=body.namespace,
            target_pod=body.target_pod,
            incident_title=body.incident_title,
            user_token=user_token,
        )
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/stream")
async def stream_investigation_endpoint(
    body: InvestigateRequest,
    user_token: str | None = Depends(get_user_token),
):
    async def event_generator():
        try:
            async for event in stream_investigation(
                namespace=body.namespace,
                target_pod=body.target_pod,
                incident_title=body.incident_title,
                user_token=user_token,
            ):
                import json

                yield {"event": "progress", "data": json.dumps(event)}
        except RuntimeError as exc:
            import json

            yield {"event": "error", "data": json.dumps({"error": str(exc)})}

    return EventSourceResponse(event_generator())


@router.get("")
async def list_investigations(
    user_token: str | None = Depends(get_user_token),
    limit: int = 20,
):
    if not user_token:
        return {"investigations": [], "message": "Auth optional — connect InsForge for history"}

    try:
        records, total = await insforge.get_records(
            "investigations",
            params={"order": "created_at.desc", "limit": str(limit)},
            user_token=user_token,
        )
        return {"investigations": records, "total": total}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"InsForge error: {exc}") from exc


@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: str,
    user_token: str | None = Depends(get_user_token),
):
    try:
        records, _ = await insforge.get_records(
            "investigations",
            params={"id": f"eq.{investigation_id}", "limit": "1"},
            user_token=user_token,
        )
        if not records:
            raise HTTPException(status_code=404, detail="Investigation not found")
        return records[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"InsForge error: {exc}") from exc
