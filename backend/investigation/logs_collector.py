"""Collect pod logs for troubleshooting."""

from __future__ import annotations

from dataclasses import dataclass

from kubernetes import client

from investigation.k8s_client import get_k8s_client


@dataclass
class PodLogs:
    pod_name: str
    namespace: str
    container: str | None
    logs: str
    truncated: bool = False


def collect_logs(
    namespace: str | None = None,
    tail_lines: int = 200,
    pod_name: str | None = None,
) -> list[PodLogs]:
    api = client.CoreV1Api(get_k8s_client())
    ns = namespace or "default"

    if pod_name:
        pods = [api.read_namespaced_pod(name=pod_name, namespace=ns)]
    else:
        pods = api.list_namespaced_pod(namespace=ns).items

    results: list[PodLogs] = []
    for pod in pods:
        containers = [c.name for c in pod.spec.containers]
        for container in containers:
            try:
                log = api.read_namespaced_pod_log(
                    name=pod.metadata.name,
                    namespace=ns,
                    container=container,
                    tail_lines=tail_lines,
                )
                truncated = len(log.splitlines()) >= tail_lines
                results.append(
                    PodLogs(
                        pod_name=pod.metadata.name,
                        namespace=ns,
                        container=container,
                        logs=log,
                        truncated=truncated,
                    )
                )
            except client.rest.ApiException:
                results.append(
                    PodLogs(
                        pod_name=pod.metadata.name,
                        namespace=ns,
                        container=container,
                        logs="(unable to retrieve logs)",
                    )
                )

    return results
