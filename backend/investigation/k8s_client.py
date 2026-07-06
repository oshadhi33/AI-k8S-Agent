"""Kubernetes client factory — supports kubeconfig, in-cluster, or explicit path."""

from __future__ import annotations

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from config import settings

_api_client: client.ApiClient | None = None


def get_k8s_client() -> client.ApiClient:
    global _api_client
    if _api_client is not None:
        return _api_client

    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except ConfigException:
                config.load_kube_config()
    except ConfigException as exc:
        raise RuntimeError(
            "Cannot connect to Kubernetes. Set KUBECONFIG_PATH or run inside a cluster."
        ) from exc

    _api_client = client.ApiClient()
    return _api_client


def reset_k8s_client() -> None:
    global _api_client
    _api_client = None
