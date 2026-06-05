import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class RootCause(BaseModel):
    observed_facts: list[str]
    inferred_reasoning: str
    summary: str


class AIAnalysis(BaseModel):
    failure_category: str
    root_cause: RootCause
    severity: str
    severity_rationale: str
    is_flaky: bool
    flakiness_indicators: list[str]
    debugging_steps: list[str]
    confidence_score: float
    low_confidence_reasons: list[str]
    suggested_fix: Optional[str]
    related_components: list[str]


class BuildInsight(BaseModel):
    build_at_risk: bool
    risk_level: str
    risk_rationale: str
    likely_regression_commit: Optional[str]
    regression_reasoning: str
    affected_components: list[str]
    recommended_action: str
    action_rationale: str
    confidence_score: float
    patterns_detected: list[str]


class TestCaseResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    suite_name: str
    classname: str
    name: str
    duration: float
    status: str
    failure_message: Optional[str]
    failure_type: Optional[str]
    stack_trace: Optional[str]
    failure_category: Optional[str]
    root_cause_summary: Optional[str]
    severity: Optional[str]
    is_flaky: bool
    confidence_score: Optional[float]
    ai_analysis: Optional[dict[str, Any]]
    cluster_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: uuid.UUID
    run_id: str
    status: str
    build_id: str
    job_name: str
    git_commit: str
    branch: str
    environment: str
    jenkins_url: Optional[str]
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    build_at_risk: bool
    risk_level: Optional[str]
    regression_commit: Optional[str]
    build_insight: Optional[dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FlakyTestResponse(BaseModel):
    id: uuid.UUID
    test_name: str
    classname: str
    job_name: str
    fail_count: int
    pass_count: int
    total_runs: int
    flakiness_score: float
    indicators: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    test_case_id: uuid.UUID
    engineer_email: Optional[str] = None
    correct_category: Optional[str] = None
    correct_severity: Optional[str] = None
    feedback_notes: Optional[str] = None
    is_helpful: bool = True
