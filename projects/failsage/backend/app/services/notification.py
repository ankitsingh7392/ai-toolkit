import logging
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_slack_notification(
    run_id: str,
    job_name: str,
    build_id: str,
    failed: int,
    risk_level: Optional[str],
    build_at_risk: bool,
) -> None:
    if not settings.slack_webhook_url:
        return

    color = "#FF0000" if build_at_risk else "#FFA500"
    risk_text = f"*Risk:* {risk_level}" if risk_level else ""

    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"QE Intelligence: {job_name} #{build_id}",
                "text": f"{failed} test(s) failed. {risk_text}",
                "fields": [
                    {"title": "Run ID", "value": run_id, "short": True},
                    {"title": "Action", "value": "INVESTIGATE" if build_at_risk else "MONITOR", "short": True},
                ],
                "footer": "FailSage",
            }
        ]
    }

    try:
        with httpx.Client(timeout=5) as client:
            client.post(settings.slack_webhook_url, json=payload)
    except Exception as exc:
        logger.warning("Slack notification failed: %s", exc)


def create_jira_ticket(
    test_name: str,
    classname: str,
    root_cause: str,
    severity: str,
    run_id: str,
    ci_metadata: dict[str, Any],
) -> Optional[str]:
    if not settings.jira_url or not settings.jira_token:
        return None

    priority_map = {"P0": "Blocker", "P1": "Critical", "P2": "Major", "P3": "Minor"}

    payload = {
        "fields": {
            "project": {"key": settings.jira_project},
            "issuetype": {"name": "Bug"},
            "summary": f"[QE Auto] {test_name} — {root_cause[:80]}",
            "description": (
                f"*Auto-created by FailSage*\n\n"
                f"*Test:* {classname}::{test_name}\n"
                f"*Run ID:* {run_id}\n"
                f"*Branch:* {ci_metadata.get('branch', 'unknown')}\n"
                f"*Commit:* {ci_metadata.get('git_commit', 'unknown')}\n\n"
                f"*Root Cause:* {root_cause}"
            ),
            "priority": {"name": priority_map.get(severity, "Major")},
            "labels": ["auto-triage", "failsage"],
        }
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"{settings.jira_url}/rest/api/2/issue",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.jira_token}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json().get("key")
    except Exception as exc:
        logger.warning("Jira ticket creation failed: %s", exc)
        return None
