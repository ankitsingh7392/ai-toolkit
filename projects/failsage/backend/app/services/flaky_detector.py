import re
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db.flaky import FlakyTest
from app.models.db.test_case import TestCase

settings = get_settings()

FLAKY_PATTERNS = [
    r"connection (timed out|refused|reset)",
    r"socket (timeout|error)",
    r"flaky|intermittent|unstable",
    r"element not (found|interactable|clickable)",
    r"stale element",
    r"no such (window|frame|element)",
    r"timeout.*waiting",
    r"could not establish connection",
    r"race condition",
    r"too many requests",
    r"503|502 bad gateway",
]

_FLAKY_RE = re.compile("|".join(FLAKY_PATTERNS), re.IGNORECASE)


def _matches_flaky_pattern(message: Optional[str]) -> list[str]:
    if not message:
        return []
    return [p for p in FLAKY_PATTERNS if re.search(p, message, re.IGNORECASE)]


def compute_flakiness_score(fail_count: int, pass_count: int) -> float:
    total = fail_count + pass_count
    if total == 0:
        return 0.0
    fail_rate = fail_count / total
    # Penalise alternating runs more than consistently failing tests
    # Score peaks at ~50% fail rate (true flaky behavior)
    return round(1.0 - abs(fail_rate - 0.5) * 2, 4)


def upsert_flaky_record(
    session: Session,
    test_name: str,
    classname: str,
    job_name: str,
    current_status: str,
    failure_message: Optional[str],
) -> FlakyTest:
    record = session.execute(
        select(FlakyTest).where(
            FlakyTest.test_name == test_name,
            FlakyTest.job_name == job_name,
        )
    ).scalar_one_or_none()

    pattern_hits = _matches_flaky_pattern(failure_message)

    if record is None:
        record = FlakyTest(
            test_name=test_name,
            classname=classname,
            job_name=job_name,
            fail_count=1 if current_status in ("failed", "error") else 0,
            pass_count=1 if current_status == "passed" else 0,
            total_runs=1,
            indicators={"pattern_hits": pattern_hits},
        )
        session.add(record)
    else:
        if current_status in ("failed", "error"):
            record.fail_count += 1
        elif current_status == "passed":
            record.pass_count += 1
        record.total_runs += 1
        record.indicators = {"pattern_hits": pattern_hits}

    record.flakiness_score = compute_flakiness_score(record.fail_count, record.pass_count)
    return record


def is_flaky(
    session: Session,
    test_name: str,
    job_name: str,
    failure_message: Optional[str],
) -> tuple[bool, list[str]]:
    """Returns (is_flaky, list_of_indicators)."""
    indicators: list[str] = []

    pattern_hits = _matches_flaky_pattern(failure_message)
    if pattern_hits:
        indicators.append(f"matches flaky error pattern: {pattern_hits[0]}")

    record = session.execute(
        select(FlakyTest).where(
            FlakyTest.test_name == test_name,
            FlakyTest.job_name == job_name,
        )
    ).scalar_one_or_none()

    if record and record.total_runs >= 3:
        fail_rate = record.fail_count / record.total_runs
        if 0.1 < fail_rate < 0.9:
            indicators.append(
                f"fail rate {fail_rate:.0%} over {record.total_runs} runs (inconsistent)"
            )
        if record.flakiness_score >= 0.6:
            indicators.append(f"flakiness score {record.flakiness_score:.2f}")

    return bool(indicators), indicators
