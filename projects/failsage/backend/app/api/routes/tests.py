import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db.test_case import TestCase
from app.models.schemas.analysis import TestCaseResponse

router = APIRouter(prefix="/test", tags=["Test Analysis"])


@router.get("/{test_id}/analysis", response_model=TestCaseResponse, summary="Full AI analysis for a test case")  # noqa: E501
async def get_test_analysis(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TestCaseResponse:
    row = (
        await db.execute(select(TestCase).where(TestCase.id == test_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    return TestCaseResponse.model_validate(row)
