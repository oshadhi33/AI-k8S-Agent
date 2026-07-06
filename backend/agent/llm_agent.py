"""LLM reasoning via OpenRouter (key provisioned through InsForge)."""

from __future__ import annotations

import json
import re

from openai import AsyncOpenAI

from agent.prompt_builder import build_prompt
from config import settings


async def analyze_with_llm(evidence: dict) -> dict:
    if not settings.openrouter_api_key:
        return _fallback_analysis(evidence)

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )

    messages = build_prompt(evidence)
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            return json.loads(match.group())
        return _fallback_analysis(evidence)


def _fallback_analysis(evidence: dict) -> dict:
    """Rule-based fallback when OpenRouter is not configured."""
    pods = evidence.get("pods", [])
    issues: list[str] = []
    problem_type = "Unknown"

    for pod in pods:
        for issue in pod.get("issues", []):
            issues.append(f"{pod['name']}: {issue}")
            if "CrashLoopBackOff" in issue:
                problem_type = "CrashLoopBackOff"
            elif "ImagePullBackOff" in issue or "image pull" in issue.lower():
                problem_type = "ImagePullBackOff"
            elif "OOMKilled" in issue:
                problem_type = "OOMKilled"
            elif "Pending" in issue:
                problem_type = "Pending Pods"

    failure_events = [e for e in evidence.get("events", []) if e.get("is_failure")]
    if failure_events and problem_type == "Unknown":
        problem_type = failure_events[0].get("reason", "Unknown")

    root_cause = issues[0] if issues else "No obvious issues detected in collected evidence"
    if failure_events:
        root_cause = failure_events[0].get("message", root_cause)

    return {
        "root_cause": root_cause,
        "problem_type": problem_type,
        "confidence": 60 if issues else 30,
        "analysis": (
            "Rule-based analysis (OpenRouter not configured). "
            f"Found {len(issues)} pod issues and {len(failure_events)} failure events."
        ),
        "suggested_fixes": [
            {
                "type": "kubectl",
                "description": "Describe failing pod for details",
                "command_or_patch": f"kubectl describe pod <pod-name> -n {evidence.get('namespace', 'default')}",
            }
        ],
        "prevention": ["Configure OPENROUTER_API_KEY for AI-powered root cause analysis"],
        "affected_resources": [p["name"] for p in pods if p.get("issues")],
    }
