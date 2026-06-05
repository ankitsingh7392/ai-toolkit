"""Standalone parser unit tests — no Docker needed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.junit_parser import parse_junit_xml  # noqa: E402

SAMPLE = (Path(__file__).parent / "sample_junit.xml").read_text()


def test_total_counts():
    r = parse_junit_xml(SAMPLE)
    assert r.total_tests == 15
    assert r.total_failed == 7
    assert r.total_errors == 1
    assert r.total_skipped == 1
    assert r.total_passed == 6


def test_failure_has_stack_trace():
    r = parse_junit_xml(SAMPLE)
    failures = [tc for s in r.suites for tc in s.test_cases if tc.status == "failed"]
    assert all(tc.stack_trace for tc in failures)


def test_skipped_parsed():
    r = parse_junit_xml(SAMPLE)
    skipped = [tc for s in r.suites for tc in s.test_cases if tc.status == "skipped"]
    assert len(skipped) == 1
    assert "MFA" in (skipped[0].failure_message or "")


def test_error_parsed():
    r = parse_junit_xml(SAMPLE)
    errors = [tc for s in r.suites for tc in s.test_cases if tc.status == "error"]
    assert len(errors) == 1
    assert "5432" in errors[0].stack_trace


if __name__ == "__main__":
    test_total_counts()
    test_failure_has_stack_trace()
    test_skipped_parsed()
    test_error_parsed()
    print("All parser tests passed ✓")
