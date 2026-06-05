from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db.feedback import Feedback
from app.models.db.flaky import FlakyTest
from app.models.schemas.analysis import FeedbackRequest, FlakyTestResponse

router = APIRouter(tags=["Feedback & Flaky Tests"])


@router.post("/feedback", status_code=status.HTTP_201_CREATED, summary="QE engineer feedback loop")
async def submit_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    fb = Feedback(
        test_case_id=body.test_case_id,
        engineer_email=body.engineer_email,
        correct_category=body.correct_category,
        correct_severity=body.correct_severity,
        feedback_notes=body.feedback_notes,
        is_helpful=body.is_helpful,
    )
    db.add(fb)
    return {"message": "Feedback recorded. Thank you."}


@router.get("/flaky-tests", response_model=list[FlakyTestResponse], summary="Known flaky tests")
async def list_flaky_tests(
    job_name: str | None = Query(None),
    min_score: float = Query(0.4, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[FlakyTestResponse]:
    q = select(FlakyTest).where(FlakyTest.flakiness_score >= min_score).limit(limit)
    if job_name:
        q = q.where(FlakyTest.job_name == job_name)
    rows = (await db.execute(q)).scalars().all()
    return [FlakyTestResponse.model_validate(r) for r in rows]
