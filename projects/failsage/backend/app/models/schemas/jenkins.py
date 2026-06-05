from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CIMetadata(BaseModel):
    build_id: str = Field(..., description="Jenkins build number, e.g. '1042'")
    job_name: str = Field(..., description="Jenkins job name, e.g. 'backend-regression'")
    git_commit: str = Field(..., min_length=7, max_length=40, description="Full or short git SHA")
    branch: str = Field(..., description="e.g. 'main', 'feature/login-refactor'")
    environment: str = Field(..., description="e.g. 'staging', 'qa', 'prod'")
    jenkins_url: Optional[str] = Field(None, description="Link to the Jenkins build")

    @field_validator("git_commit")
    @classmethod
    def strip_commit(cls, v: str) -> str:
        return v.strip()


class JenkinsWebhookPayload(BaseModel):
    ci: CIMetadata
    junit_xml: str = Field(..., description="Raw JUnit XML content as a string")
    additional_logs: Optional[str] = Field(None, description="Extra logs/stack traces")
    bug_description: Optional[str] = Field(None, description="Optional Jira or manual context")


class RunCreatedResponse(BaseModel):
    run_id: str
    status: str
    message: str
    polling_url: str
