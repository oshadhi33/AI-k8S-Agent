"""Orchestrate all investigation collectors into structured evidence."""

from __future__ import annotations

from dataclasses import asdict

from investigation.deployment_inspector import inspect_deployments
from investigation.events_analyzer import analyze_events
from investigation.logs_collector import collect_logs
from investigation.network_inspector import inspect_network
from investigation.pod_inspector import inspect_pods


def run_investigation(
    namespace: str = "default",
    target_pod: str | None = None,
    incident_title: str | None = None,
) -> dict:
    pods = inspect_pods(namespace)
    logs = collect_logs(namespace=namespace, pod_name=target_pod)
    events = analyze_events(namespace)
    deployments = inspect_deployments(namespace)
    services = inspect_network(namespace)

    unhealthy_pods = [p for p in pods if p.issues or p.phase not in ("Running", "Succeeded")]
    failure_events = [e for e in events if e.is_failure]

    return {
        "incident_title": incident_title or f"Investigation in {namespace}",
        "namespace": namespace,
        "target_pod": target_pod,
        "summary": {
            "total_pods": len(pods),
            "unhealthy_pods": len(unhealthy_pods),
            "failure_events": len(failure_events),
            "deployments_with_issues": sum(1 for d in deployments if d.issues),
            "services_with_issues": sum(1 for s in services if s.issues),
        },
        "pods": [asdict(p) for p in pods],
        "logs": [asdict(l) for l in logs],
        "events": [asdict(e) for e in events[:50]],
        "deployments": [asdict(d) for d in deployments],
        "services": [asdict(s) for s in services],
    }
