import json
import logging
from typing import Any, Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FAILURE_ANALYSIS_PROMPT = """You are a QE intelligence engine embedded in a CI/CD pipeline.
Analyze the test failure below and return ONLY valid JSON — no prose, no markdown, no text outside JSON.

STRICT RULES:
1. Base your analysis ONLY on the data provided — never invent context not present
2. Separate observed_facts (directly in the data) from inferred_reasoning (your deduction)
3. If data is insufficient to determine something, use null and lower confidence_score
4. failure_category must be exactly one of: UI, API, Database, Performance, Infrastructure, TestIssue

TEST FAILURE:
{failure_data}

CI METADATA:
{ci_metadata}

HISTORICAL CONTEXT (last runs for this test):
{history}

Return this EXACT JSON schema:
{{
  "failure_category": "<UI|API|Database|Performance|Infrastructure|TestIssue>",
  "root_cause": {{
    "observed_facts": ["<exact strings from the provided data>"],
    "inferred_reasoning": "<your deduction from those facts>",
    "summary": "<one-sentence root cause>"
  }},
  "severity": "<P0|P1|P2|P3>",
  "severity_rationale": "<why this severity>",
  "is_flaky": <true|false>,
  "flakiness_indicators": ["<signals suggesting flakiness, or empty list>"],
  "debugging_steps": ["<ordered investigation step 1>", "<step 2>"],
  "confidence_score": <0-100>,
  "low_confidence_reasons": ["<what limits confidence, or empty list>"],
  "suggested_fix": "<specific fix if determinable, else null>",
  "related_components": ["<system components from classname/error context>"]
}}"""

BUILD_REGRESSION_PROMPT = """You are a CI/CD regression analyst. Assess this Jenkins build's health and regression risk.
Return ONLY valid JSON.

CI METADATA:
{ci_metadata}

FAILURE SUMMARY ({failure_count} failures):
{failure_summary}

FAILURE CLUSTERS:
{clusters}

Return this EXACT JSON schema:
{{
  "build_at_risk": <true|false>,
  "risk_level": "<CRITICAL|HIGH|MEDIUM|LOW>",
  "risk_rationale": "<evidence for this risk level>",
  "likely_regression_commit": "<SHA if determinable from context, else null>",
  "regression_reasoning": "<evidence or null>",
  "affected_components": ["<component names from classnames/error context>"],
  "recommended_action": "<BLOCK_MERGE|INVESTIGATE|MONITOR|PASS>",
  "action_rationale": "<why this action>",
  "confidence_score": <0-100>,
  "patterns_detected": ["<cross-test patterns observed>"]
}}"""

MOCK_ANALYSIS: dict[str, Any] = {
    "failure_category": "API",
    "root_cause": {
        "observed_facts": ["HTTP 500 returned from /api/users endpoint", "NullPointerException in UserService.getById"],
        "inferred_reasoning": "The service is not handling a null user lookup result before accessing its properties.",
        "summary": "Unhandled null dereference in UserService.getById when user does not exist",
    },
    "severity": "P1",
    "severity_rationale": "Core user API is broken; affects all flows dependent on user retrieval",
    "is_flaky": False,
    "flakiness_indicators": [],
    "debugging_steps": [
        "Check UserService.getById for null guard before property access",
        "Review recent commits to UserService (git log -p src/UserService.java)",
        "Verify test data: does the test user exist in the test DB?",
        "Run the test in isolation to rule out test-order dependency",
    ],
    "confidence_score": 72,
    "low_confidence_reasons": ["No database state visible in provided logs"],
    "suggested_fix": "Add null check: if (user == null) throw new UserNotFoundException(id);",
    "related_components": ["UserService", "UserController", "UserRepository"],
}

MOCK_BUILD_INSIGHT: dict[str, Any] = {
    "build_at_risk": True,
    "risk_level": "HIGH",
    "risk_rationale": "3 of 5 failures share the same API error pattern suggesting a recent regression",
    "likely_regression_commit": None,
    "regression_reasoning": "Failures cluster around UserService; no commit SHA available in provided metadata",
    "affected_components": ["UserService", "AuthController"],
    "recommended_action": "INVESTIGATE",
    "action_rationale": "Pattern suggests a single root cause; investigate before merging",
    "confidence_score": 65,
    "patterns_detected": ["Multiple tests failing with NullPointerException in the same service"],
}


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_claude(prompt: str) -> dict[str, Any]:
    client = _get_client()
    message = client.messages.create(
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    # Strip any accidental markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def analyze_failure(
    *,
    suite_name: str,
    classname: str,
    test_name: str,
    failure_message: Optional[str],
    failure_type: Optional[str],
    stack_trace: Optional[str],
    system_out: Optional[str],
    ci_metadata: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    use_mock = settings.ai_mock_mode or not settings.anthropic_api_key

    if use_mock:
        logger.info("AI mock mode: returning deterministic analysis for %s", test_name)
        return MOCK_ANALYSIS

    failure_data = {
        "suite": suite_name,
        "classname": classname,
        "test_name": test_name,
        "failure_type": failure_type,
        "failure_message": failure_message,
        "stack_trace": (stack_trace or "")[:3000],
        "system_out": (system_out or "")[:1000],
    }

    prompt = FAILURE_ANALYSIS_PROMPT.format(
        failure_data=json.dumps(failure_data, indent=2),
        ci_metadata=json.dumps(ci_metadata, indent=2),
        history=json.dumps(history[-5:], indent=2) if history else "[]",
    )

    try:
        return _call_claude(prompt)
    except Exception as exc:
        logger.exception("AI failure analysis failed: %s", exc)
        return {**MOCK_ANALYSIS, "confidence_score": 0, "low_confidence_reasons": [f"AI unavailable: {exc}"]}


def analyze_build(
    *,
    ci_metadata: dict[str, Any],
    failure_summaries: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> dict[str, Any]:
    use_mock = settings.ai_mock_mode or not settings.anthropic_api_key

    if use_mock:
        logger.info("AI mock mode: returning deterministic build insight")
        return MOCK_BUILD_INSIGHT

    prompt = BUILD_REGRESSION_PROMPT.format(
        ci_metadata=json.dumps(ci_metadata, indent=2),
        failure_count=len(failure_summaries),
        failure_summary=json.dumps(failure_summaries[:20], indent=2),
        clusters=json.dumps(clusters, indent=2),
    )

    try:
        return _call_claude(prompt)
    except Exception as exc:
        logger.exception("AI build analysis failed: %s", exc)
        return {**MOCK_BUILD_INSIGHT, "confidence_score": 0, "risk_rationale": f"AI unavailable: {exc}"}
