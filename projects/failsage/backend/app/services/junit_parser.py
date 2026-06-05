from dataclasses import dataclass, field
from typing import Optional

import defusedxml.ElementTree as ET


@dataclass
class ParsedTestCase:
    suite_name: str
    classname: str
    name: str
    time: float
    status: str
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    stack_trace: Optional[str] = None
    system_out: Optional[str] = None
    system_err: Optional[str] = None


@dataclass
class ParsedSuite:
    name: str
    tests: int
    failures: int
    errors: int
    skipped: int
    time: float
    test_cases: list[ParsedTestCase] = field(default_factory=list)


@dataclass
class ParseResult:
    suites: list[ParsedSuite] = field(default_factory=list)
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_errors: int = 0
    total_skipped: int = 0


def parse_junit_xml(xml_content: str) -> ParseResult:
    root = ET.fromstring(xml_content)
    result = ParseResult()

    if root.tag == "testsuites":
        suite_elements = root.findall("testsuite")
        # Some suites nest further — flatten one level
        for se in list(suite_elements):
            suite_elements.extend(se.findall("testsuite"))
    elif root.tag == "testsuite":
        suite_elements = [root]
        suite_elements.extend(root.findall("testsuite"))
    else:
        raise ValueError(f"Unexpected root element: {root.tag}")

    seen = set()
    for se in suite_elements:
        eid = id(se)
        if eid in seen:
            continue
        seen.add(eid)
        suite = _parse_suite(se)
        if suite.test_cases:
            result.suites.append(suite)
            result.total_tests += len(suite.test_cases)
            for tc in suite.test_cases:
                if tc.status == "failed":
                    result.total_failed += 1
                elif tc.status == "error":
                    result.total_errors += 1
                elif tc.status == "skipped":
                    result.total_skipped += 1
                else:
                    result.total_passed += 1

    return result


def _parse_suite(se) -> ParsedSuite:
    suite = ParsedSuite(
        name=se.get("name", "unknown"),
        tests=int(se.get("tests", 0) or 0),
        failures=int(se.get("failures", 0) or 0),
        errors=int(se.get("errors", 0) or 0),
        skipped=int(se.get("skipped", 0) or 0),
        time=float(se.get("time", 0.0) or 0.0),
    )
    for tc_elem in se.findall("testcase"):
        suite.test_cases.append(_parse_test_case(suite.name, tc_elem))
    return suite


def _parse_test_case(suite_name: str, tc) -> ParsedTestCase:
    failure_elem = tc.find("failure")
    error_elem = tc.find("error")
    skipped_elem = tc.find("skipped")

    status = "passed"
    failure_message = failure_type = stack_trace = None

    if failure_elem is not None:
        status = "failed"
        failure_message = failure_elem.get("message", "")
        failure_type = failure_elem.get("type", "")
        stack_trace = (failure_elem.text or "").strip()
    elif error_elem is not None:
        status = "error"
        failure_message = error_elem.get("message", "")
        failure_type = error_elem.get("type", "")
        stack_trace = (error_elem.text or "").strip()
    elif skipped_elem is not None:
        status = "skipped"
        failure_message = skipped_elem.get("message", "")

    return ParsedTestCase(
        suite_name=suite_name,
        classname=tc.get("classname", ""),
        name=tc.get("name", ""),
        time=float(tc.get("time", 0.0) or 0.0),
        status=status,
        failure_message=failure_message,
        failure_type=failure_type,
        stack_trace=stack_trace,
        system_out=(tc.findtext("system-out") or "").strip() or None,
        system_err=(tc.findtext("system-err") or "").strip() or None,
    )
