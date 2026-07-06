"""Network inspection — services, selectors, endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field

from kubernetes import client

from investigation.k8s_client import get_k8s_client


@dataclass
class ServiceFinding:
    name: str
    namespace: str
    type: str
    cluster_ip: str | None
    selector: dict
    ports: list[dict]
    endpoint_count: int
    issues: list[str] = field(default_factory=list)


def inspect_network(namespace: str | None = None) -> list[ServiceFinding]:
    core = client.CoreV1Api(get_k8s_client())
    ns = namespace or "default"

    services = core.list_namespaced_service(namespace=ns)
    endpoints_list = {
        (ep.metadata.name, ep.metadata.namespace): ep
        for ep in core.list_namespaced_endpoints(namespace=ns).items
    }

    findings: list[ServiceFinding] = []
    for svc in services.items:
        selector = svc.spec.selector or {}
        ports = [
            {"port": p.port, "target_port": str(p.target_port), "protocol": p.protocol}
            for p in svc.spec.ports or []
        ]

        ep = endpoints_list.get((svc.metadata.name, svc.metadata.namespace))
        endpoint_count = 0
        if ep and ep.subsets:
            for subset in ep.subsets:
                endpoint_count += len(subset.addresses or [])

        issues: list[str] = []
        if selector and endpoint_count == 0:
            issues.append("Service has selector but no ready endpoints — possible selector mismatch")
        if not selector and svc.spec.type != "ExternalName":
            issues.append("Service has no selector — may rely on manual Endpoints")

        findings.append(
            ServiceFinding(
                name=svc.metadata.name,
                namespace=svc.metadata.namespace,
                type=svc.spec.type,
                cluster_ip=svc.spec.cluster_ip,
                selector=selector,
                ports=ports,
                endpoint_count=endpoint_count,
                issues=issues,
            )
        )

    return findings
