"""Inspect deployment rollout health."""

from __future__ import annotations

from dataclasses import dataclass, field

from kubernetes import client

from investigation.k8s_client import get_k8s_client


@dataclass
class DeploymentFinding:
    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    updated_replicas: int
    conditions: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def inspect_deployments(namespace: str | None = None) -> list[DeploymentFinding]:
    api = client.AppsV1Api(get_k8s_client())
    ns = namespace or "default"
    deployments = api.list_namespaced_deployment(namespace=ns)

    findings: list[DeploymentFinding] = []
    for dep in deployments.items:
        status = dep.status
        spec_replicas = dep.spec.replicas or 0
        ready = status.ready_replicas or 0
        available = status.available_replicas or 0
        updated = status.updated_replicas or 0

        issues: list[str] = []
        if ready < spec_replicas:
            issues.append(f"Only {ready}/{spec_replicas} replicas ready")
        if updated < spec_replicas:
            issues.append(f"Rollout incomplete: {updated}/{spec_replicas} updated")
        if available < spec_replicas:
            issues.append(f"Only {available}/{spec_replicas} available")

        conditions = []
        for cond in status.conditions or []:
            conditions.append(
                {
                    "type": cond.type,
                    "status": cond.status,
                    "reason": cond.reason,
                    "message": cond.message,
                }
            )
            if cond.status == "False" and cond.type in ("Progressing", "Available"):
                issues.append(f"{cond.type}={cond.status}: {cond.reason} — {cond.message}")

        findings.append(
            DeploymentFinding(
                name=dep.metadata.name,
                namespace=dep.metadata.namespace,
                replicas=spec_replicas,
                ready_replicas=ready,
                available_replicas=available,
                updated_replicas=updated,
                conditions=conditions,
                issues=issues,
            )
        )

    return findings
