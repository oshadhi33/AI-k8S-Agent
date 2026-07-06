"""Investigation orchestration with progress updates and history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Callable, Awaitable

from agent.llm_agent import analyze_with_llm
from config import settings
from insforge_client import insforge
from investigation.orchestrator import run_investigation

ProgressCallback = Callable[[str, str], Awaitable[None]]

STEPS = [
    ("checking_pods", "Checking pods"),
    ("reading_logs", "Reading logs"),
    ("analyzing_events", "Analyzing events"),
    ("inspecting_deployments", "Inspecting deployments"),
    ("checking_network", "Checking networking"),
    ("finding_root_cause", "Finding root cause"),
]


async def _noop_progress(step: str, message: str) -> None:
    pass


async def _publish_progress(
    investigation_id: str,
    step: str,
    message: str,
    status: str = "in_progress",
    user_token: str | None = None,
) -> None:
    if not settings.insforge_base_url:
        return
    channel = f"investigation:{investigation_id}"
    await insforge.publish_message(
        channel,
        {
            "investigation_id": investigation_id,
            "step": step,
            "message": message,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        user_token=user_token,
    )


async def run_full_investigation(
    namespace: str = "default",
    target_pod: str | None = None,
    incident_title: str | None = None,
    user_token: str | None = None,
    on_progress: ProgressCallback | None = None,
) -> dict:
    progress = on_progress or _noop_progress
    investigation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": investigation_id,
        "title": incident_title or f"Investigation in {namespace}",
        "namespace": namespace,
        "target_pod": target_pod,
        "status": "investigating",
        "created_at": now,
    }

    if settings.insforge_base_url:
        try:
            await insforge.create_records("investigations", [record], user_token)
        except Exception:
            pass

    async def step(name: str, msg: str) -> None:
        await progress(name, msg)
        await _publish_progress(investigation_id, name, msg, user_token=user_token)

    await step("checking_pods", STEPS[0][1])
    evidence = run_investigation(namespace, target_pod, incident_title)

    await step("reading_logs", STEPS[1][1])
    await step("analyzing_events", STEPS[2][1])
    await step("inspecting_deployments", STEPS[3][1])
    await step("checking_network", STEPS[4][1])
    await step("finding_root_cause", STEPS[5][1])

    analysis = await analyze_with_llm(evidence)

    result = {
        "id": investigation_id,
        "title": record["title"],
        "namespace": namespace,
        "target_pod": target_pod,
        "status": "completed",
        "evidence_summary": evidence.get("summary"),
        "root_cause": analysis.get("root_cause"),
        "problem_type": analysis.get("problem_type"),
        "confidence": analysis.get("confidence"),
        "analysis": analysis.get("analysis"),
        "suggested_fixes": analysis.get("suggested_fixes", []),
        "prevention": analysis.get("prevention", []),
        "affected_resources": analysis.get("affected_resources", []),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    if settings.insforge_base_url:
        try:
            await insforge.update_records(
                "investigations",
                {"id": f"eq.{investigation_id}"},
                {
                    "status": "completed",
                    "root_cause": result["root_cause"],
                    "problem_type": result["problem_type"],
                    "confidence": result["confidence"],
                    "analysis": result["analysis"],
                    "suggested_fixes": result["suggested_fixes"],
                    "prevention": result["prevention"],
                    "affected_resources": result["affected_resources"],
                    "evidence_summary": result["evidence_summary"],
                    "completed_at": result["completed_at"],
                },
                user_token,
            )
        except Exception:
            pass

    await _publish_progress(
        investigation_id, "completed", "Investigation complete", "completed", user_token
    )

    return result


async def stream_investigation(
    namespace: str = "default",
    target_pod: str | None = None,
    incident_title: str | None = None,
    user_token: str | None = None,
) -> AsyncGenerator[dict, None]:
    progress_queue: list[dict] = []

    async def on_progress(step: str, message: str) -> None:
        progress_queue.append({"step": step, "message": message, "status": "in_progress"})

    import asyncio

    task = asyncio.create_task(
        run_full_investigation(
            namespace=namespace,
            target_pod=target_pod,
            incident_title=incident_title,
            user_token=user_token,
            on_progress=on_progress,
        )
    )

    seen = 0
    while not task.done():
        while seen < len(progress_queue):
            yield progress_queue[seen]
            seen += 1
        await asyncio.sleep(0.1)

    while seen < len(progress_queue):
        yield progress_queue[seen]
        seen += 1

    result = await task
    yield {"step": "result", "status": "completed", "result": result}
