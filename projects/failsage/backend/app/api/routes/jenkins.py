import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db.run import TestRun
from app.models.schemas.jenkins import JenkinsWebhookPayload, RunCreatedResponse
from app.tasks.analysis import process_jenkins_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ci/jenkins", tags=["Jenkins Integration"])


@router.post(
    "/test-results",
    response_model=RunCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive JUnit XML test results from Jenkins",
)
async def ingest_test_results(
    payload: JenkinsWebhookPayload,
    db: AsyncSession = Depends(get_db),
) -> RunCreatedResponse:
    """
    Non-blocking Jenkins webhook endpoint.
    Returns a run_id immediately; analysis proceeds asynchronously.
    """
    run_id = secrets.token_hex(16)

    run = TestRun(
        run_id=run_id,
        status="pending",
        build_id=payload.ci.build_id,
        job_name=payload.ci.job_name,
        git_commit=payload.ci.git_commit,
        branch=payload.ci.branch,
        environment=payload.ci.environment,
        jenkins_url=payload.ci.jenkins_url,
    )
    db.add(run)
    await db.flush()

    ci_meta = payload.ci.model_dump()
    process_jenkins_run.delay(run_id, payload.junit_xml, ci_meta)

    logger.info(
        "Queued analysis run_id=%s for job=%s build=%s",
        run_id, payload.ci.job_name, payload.ci.build_id,
    )

    return RunCreatedResponse(
        run_id=run_id,
        status="pending",
        message="Analysis queued. Use the polling_url to track progress.",
        polling_url=f"/runs/{run_id}",
    )
