"""Convert investigation evidence into an LLM prompt."""

from __future__ import annotations

import json

SYSTEM_PROMPT = """You are an expert Kubernetes SRE and troubleshooting agent.

Analyze the provided cluster investigation data (pods, logs, events, deployments, services).
Your job:
1. Identify the PRIMARY root cause (not just symptoms)
2. Correlate signals across pods, events, logs, and deployments
3. Provide actionable fix recommendations (kubectl commands and YAML changes)
4. Assign a confidence score (0-100) for your diagnosis
5. Suggest prevention measures

Respond ONLY with valid JSON matching this schema:
{
  "root_cause": "string — concise primary root cause",
  "problem_type": "string — e.g. CrashLoopBackOff, ImagePullBackOff, OOMKilled, etc.",
  "confidence": number,
  "analysis": "string — detailed explanation correlating evidence",
  "suggested_fixes": [
    {"type": "kubectl|yaml|config", "description": "string", "command_or_patch": "string"}
  ],
  "prevention": ["string"],
  "affected_resources": ["string"]
}

Supported problem types include: CrashLoopBackOff, ImagePullBackOff, OOMKilled, Pending Pods,
Resource Exhaustion, Deployment Rollout Failures, Service Selector Mismatch, DNS Resolution Problems,
Readiness/Liveness Probe Failures, Networking Issues."""


def build_prompt(evidence: dict) -> list[dict]:
    user_content = f"""Investigate this Kubernetes incident and determine the root cause.

## Incident
Title: {evidence.get('incident_title', 'Unknown')}
Namespace: {evidence.get('namespace', 'default')}
Target Pod: {evidence.get('target_pod') or 'all pods in namespace'}

## Summary
{json.dumps(evidence.get('summary', {}), indent=2)}

## Pods
{json.dumps(evidence.get('pods', []), indent=2)}

## Recent Events (failures highlighted)
{json.dumps([e for e in evidence.get('events', []) if e.get('is_failure')][:20], indent=2)}

## Logs (sample)
{json.dumps(evidence.get('logs', [])[:5], indent=2)}

## Deployments
{json.dumps(evidence.get('deployments', []), indent=2)}

## Services / Networking
{json.dumps(evidence.get('services', []), indent=2)}
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
