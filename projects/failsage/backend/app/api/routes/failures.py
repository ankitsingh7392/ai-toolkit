from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db.run import TestRun
from app.models.db.test_case import TestCase
from app.models.schemas.analysis import TestCaseResponse

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("/{run_id}", response_model=list[TestCaseResponse], summary="All failures for a run")
async def get_failures(
    run_id: str,
    severity: Optional[str] = Query(None, description="Filter by P0/P1/P2/P3"),
    category: Optional[str] = Query(None, description="Filter by failure_category"),
    flaky_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list[TestCaseResponse]:
    run_row = (await db.execute(select(TestRun.id).where(TestRun.run_id == run_id))).scalar_one_or_none()
    if not run_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    q = select(TestCase).where(
        TestCase.run_id == run_row,
        TestCase.status.in_(["failed", "error"]),
    )
    if severity:
        q = q.where(TestCase.severity == severity)
    if category:
        q = q.where(TestCase.failure_category == category)
    if flaky_only:
        q = q.where(TestCase.is_flaky.is_(True))

    rows = (await db.execute(q)).scalars().all()
    return [TestCaseResponse.model_validate(r) for r in rows]
