"""Analyze Kubernetes events for scheduling, image, and probe failures."""

from __future__ import annotations

from dataclasses import dataclass

from kubernetes import client

from investigation.k8s_client import get_k8s_client

WARNING_TYPES = {"Warning"}
FAILURE_REASONS = {
    "FailedScheduling",
    "FailedMount",
    "FailedAttachVolume",
    "FailedCreatePodSandBox",
    "BackOff",
    "Unhealthy",
    "Failed",
    "ErrImagePull",
    "ImagePullBackOff",
}


@dataclass
class EventFinding:
    namespace: str
    involved_object: str
    kind: str
    reason: str
    message: str
    type: str
    count: int
    is_failure: bool


def analyze_events(namespace: str | None = None, limit: int = 100) -> list[EventFinding]:
    api = client.CoreV1Api(get_k8s_client())
    ns = namespace or "default"

    events = api.list_namespaced_event(namespace=ns, limit=limit)
    findings: list[EventFinding] = []

    for ev in sorted(events.items, key=lambda e: e.last_timestamp or e.event_time or "", reverse=True):
        obj = ev.involved_object
        is_failure = ev.type in WARNING_TYPES or ev.reason in FAILURE_REASONS
        findings.append(
            EventFinding(
                namespace=ev.metadata.namespace,
                involved_object=obj.name if obj else "unknown",
                kind=obj.kind if obj else "unknown",
                reason=ev.reason,
                message=ev.message or "",
                type=ev.type,
                count=ev.count or 1,
                is_failure=is_failure,
            )
        )

    return findings
